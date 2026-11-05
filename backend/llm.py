
"""Geração com Llama + LoRA, Gemini, OpenAI ou Anthropic."""

from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    ADAPTADOR_LORA,
    MAX_NOVOS_TOKENS,
    MODELO_LLM,
    TEMPERATURA,
)


class Gerador:
    """Interface unificada para diferentes provedores de LLM."""

    PROVEDORES = ("llama", "gemini", "openai", "anthropic")

    def __init__(
        self,
        usar_lora: bool = True,
        api_key: str | None = None,
        provedor: str | None = None,
    ):
        self.provedor = (provedor or LLM_PROVIDER).lower()
        self.com_lora = False
        self.api_key = api_key

        if self.provedor not in self.PROVEDORES:
            raise ValueError(
                f"Provedor inválido: {self.provedor}. "
                f"Escolha entre: {', '.join(self.PROVEDORES)}."
            )

        if self.provedor == "llama":
            self._inicializar_llama(usar_lora)

        elif self.provedor == "gemini":
            self._inicializar_gemini()

        elif self.provedor == "openai":
            self._inicializar_openai()

        elif self.provedor == "anthropic":
            self._inicializar_anthropic()

    # -----------------------------------------
    # Inicialização do Llama
    # -----------------------------------------

    def _inicializar_llama(self, usar_lora):

        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
        )

        tem_gpu = torch.cuda.is_available()

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODELO_LLM
        )

        self.modelo = AutoModelForCausalLM.from_pretrained(
            MODELO_LLM,
            torch_dtype=(
                torch.float16 if tem_gpu else torch.float32
            ),
            device_map="auto" if tem_gpu else None,
        )

        if usar_lora and ADAPTADOR_LORA.exists():

            from peft import PeftModel

            self.modelo = PeftModel.from_pretrained(
                self.modelo,
                str(ADAPTADOR_LORA),
            )

            self.modelo = self.modelo.merge_and_unload()
            self.com_lora = True

            print("Llama carregado com adaptador LoRA.")

        elif usar_lora:

            print(
                "Aviso: adaptador LoRA não encontrado. "
                "Utilizando apenas o Llama base."
            )

        else:
            print("Llama carregado sem LoRA.")

        self.modelo.eval()

    # -----------------------------------------
    # Inicialização do Gemini
    # -----------------------------------------

    def _inicializar_gemini(self):

        from google import genai

        chave = self.api_key or GEMINI_API_KEY

        if not chave:
            raise ValueError(
                "Informe uma chave de API do Gemini."
            )

        self.client = genai.Client(api_key=chave)
        self.modelo = GEMINI_MODEL

        print(f"Gemini carregado: {self.modelo}")

    # -----------------------------------------
    # Inicialização da OpenAI
    # -----------------------------------------

    def _inicializar_openai(self):

        from openai import OpenAI

        chave = self.api_key or OPENAI_API_KEY

        if not chave:
            raise ValueError(
                "Informe uma chave de API da OpenAI."
            )

        self.client = OpenAI(api_key=chave)
        self.modelo = OPENAI_MODEL

        print(f"OpenAI carregada: {self.modelo}")

    # -----------------------------------------
    # Inicialização da Anthropic
    # -----------------------------------------

    def _inicializar_anthropic(self):

        from anthropic import Anthropic

        chave = self.api_key or ANTHROPIC_API_KEY

        if not chave:
            raise ValueError(
                "Informe uma chave de API da Anthropic."
            )

        self.client = Anthropic(api_key=chave)
        self.modelo = ANTHROPIC_MODEL

        print(f"Anthropic carregada: {self.modelo}")

    # -----------------------------------------
    # Geração com Llama
    # -----------------------------------------

    def _gerar_llama(
        self,
        mensagens,
        max_novos_tokens,
        temperatura,
    ):

        import torch

        entradas = self.tokenizer.apply_chat_template(
            mensagens,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(self.modelo.device)

        if temperatura > 0:
            amostragem = {
                "do_sample": True,
                "temperature": temperatura,
                "top_p": 0.9,
            }
        else:
            amostragem = {
                "do_sample": False,
            }

        with torch.inference_mode():

            saida = self.modelo.generate(
                **entradas,
                max_new_tokens=max_novos_tokens,
                pad_token_id=(
                    self.tokenizer.pad_token_id
                    or self.tokenizer.eos_token_id
                ),
                **amostragem,
            )

        novos = saida[0][
            entradas["input_ids"].shape[1]:
        ]

        return self.tokenizer.decode(
            novos,
            skip_special_tokens=True,
        ).strip()

    # -----------------------------------------
    # Geração com Gemini
    # -----------------------------------------

    def _gerar_gemini(
        self,
        mensagens,
        max_novos_tokens,
        temperatura,
    ):

        from google.genai import types

        instrucao_sistema = []
        historico = []

        for mensagem in mensagens:

            papel = mensagem["role"]
            conteudo = mensagem["content"]

            if papel == "system":
                instrucao_sistema.append(conteudo)

            elif papel in ("user", "assistant", "model"):

                papel_gemini = (
                    "model"
                    if papel in ("assistant", "model")
                    else "user"
                )

                historico.append(
                    types.Content(
                        role=papel_gemini,
                        parts=[
                            types.Part.from_text(text=conteudo)
                        ],
                    )
                )

            else:
                raise ValueError(
                    f"Papel de mensagem não suportado: {papel}"
                )

        configuracao = types.GenerateContentConfig(
            system_instruction=(
                "\n\n".join(instrucao_sistema) or None
            ),
            max_output_tokens=max_novos_tokens,
            temperature=temperatura,
        )

        resposta = self.client.models.generate_content(
            model=self.modelo,
            contents=historico,
            config=configuracao,
        )

        return (resposta.text or "").strip()

    # -----------------------------------------
    # Geração com OpenAI
    # -----------------------------------------

    def _gerar_openai(
        self,
        mensagens,
        max_novos_tokens,
        temperatura,
    ):

        mensagens_openai = []

        for mensagem in mensagens:

            papel = mensagem["role"]
            conteudo = mensagem["content"]

            if papel == "model":
                papel = "assistant"

            if papel not in ("system", "user", "assistant"):
                raise ValueError(
                    f"Papel de mensagem não suportado: {papel}"
                )

            mensagens_openai.append({
                "role": papel,
                "content": conteudo,
            })

        resposta = self.client.chat.completions.create(
            model=self.modelo,
            messages=mensagens_openai,
            max_tokens=max_novos_tokens,
            temperature=temperatura,
        )

        conteudo = resposta.choices[0].message.content

        return (conteudo or "").strip()

    # -----------------------------------------
    # Geração com Anthropic
    # -----------------------------------------

    def _gerar_anthropic(
        self,
        mensagens,
        max_novos_tokens,
        temperatura,
    ):

        instrucao_sistema = []
        historico = []

        for mensagem in mensagens:

            papel = mensagem["role"]
            conteudo = mensagem["content"]

            if papel == "system":
                instrucao_sistema.append(conteudo)

            elif papel in ("user", "assistant", "model"):

                papel_anthropic = (
                    "assistant"
                    if papel in ("assistant", "model")
                    else "user"
                )

                # A API Anthropic espera alternância entre user
                # e assistant. Mensagens consecutivas do mesmo
                # papel são agrupadas.
                if (
                    historico
                    and historico[-1]["role"] == papel_anthropic
                ):
                    historico[-1]["content"] += "\n\n" + conteudo
                else:
                    historico.append({
                        "role": papel_anthropic,
                        "content": conteudo,
                    })

            else:
                raise ValueError(
                    f"Papel de mensagem não suportado: {papel}"
                )

        # A API Anthropic exige que a primeira mensagem seja user.
        if not historico or historico[0]["role"] != "user":
            raise ValueError(
                "O histórico precisa começar com uma mensagem do usuário."
            )

        resposta = self.client.messages.create(
            model=self.modelo,
            max_tokens=max_novos_tokens,
            temperature=temperatura,
            system="\n\n".join(instrucao_sistema),
            messages=historico,
        )

        textos = [
            bloco.text
            for bloco in resposta.content
            if bloco.type == "text"
        ]

        return "\n".join(textos).strip()

    # -----------------------------------------
    # Interface única de geração
    # -----------------------------------------

    def gerar(
        self,
        mensagens: list[dict],
        max_novos_tokens: int = MAX_NOVOS_TOKENS,
        temperatura: float = TEMPERATURA,
    ) -> str:

        if self.provedor == "llama":
            return self._gerar_llama(
                mensagens,
                max_novos_tokens,
                temperatura,
            )

        if self.provedor == "gemini":
            return self._gerar_gemini(
                mensagens,
                max_novos_tokens,
                temperatura,
            )

        if self.provedor == "openai":
            return self._gerar_openai(
                mensagens,
                max_novos_tokens,
                temperatura,
            )

        if self.provedor == "anthropic":
            return self._gerar_anthropic(
                mensagens,
                max_novos_tokens,
                temperatura,
            )
