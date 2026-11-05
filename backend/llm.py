
"""Etapa online 3: geração com Llama + LoRA ou Gemini API."""

from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ADAPTADOR_LORA,
    MAX_NOVOS_TOKENS,
    MODELO_LLM,
    TEMPERATURA,
)


class Gerador:

    def __init__(self, usar_lora: bool = True):

        self.provedor = LLM_PROVIDER
        self.com_lora = False

        if self.provedor == "llama":
            self._inicializar_llama(usar_lora)

        elif self.provedor == "gemini":
            self._inicializar_gemini()

        else:
            raise ValueError(
                f"Provedor inválido: {self.provedor}. "
                "Escolha 'llama' ou 'gemini'."
            )

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

            # Incorpora os pesos do LoRA ao modelo.
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

        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY não encontrada no arquivo .env."
            )

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.modelo = GEMINI_MODEL

        print(f"Gemini carregado: {self.modelo}")

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

        elif self.provedor == "gemini":

            return self._gerar_gemini(
                mensagens,
                max_novos_tokens,
                temperatura,
            )
