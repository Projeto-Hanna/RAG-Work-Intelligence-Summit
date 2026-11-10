
"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

type AnalyticsReport = {
  title: string;
  summary: string;
  kpis: {
    label: string;
    value: number;
    unit?: string | null;
  }[];
  charts: {
    type: "bar" | "line";
    title: string;
    labels: string[];
    values: number[];
  }[];
  insights: {
    title: string;
    description: string;
    type: "positive" | "negative" | "neutral" | "attention";
  }[];
  sources: string[];
};

type Props = {
  report: AnalyticsReport;
};

export default function AnalyticsReportView({ report }: Props) {
  const formatarValor = (value: number, unit?: string | null) => {
    const formatted = new Intl.NumberFormat("pt-BR", {
      maximumFractionDigits: 2,
    }).format(value);

    return unit ? `${formatted} ${unit}` : formatted;
  };

  return (
    <section className="analytics-report">
      <header className="analytics-report-header">
        <h2>{report.title}</h2>
        <p>{report.summary}</p>
      </header>

      {report.kpis.length > 0 && (
        <div className="analytics-kpis">
          {report.kpis.map((kpi, index) => (
            <article className="analytics-kpi" key={index}>
              <span>{kpi.label}</span>
              <strong>
                {formatarValor(kpi.value, kpi.unit)}
              </strong>
            </article>
          ))}
        </div>
      )}

      {report.charts.map((chart, index) => {
        const data = chart.labels.map((label, i) => ({
          label,
          value: chart.values[i] ?? 0,
        }));

        return (
          <article className="analytics-chart" key={index}>
            <h3>{chart.title}</h3>

            <div className="analytics-chart-container">
              <ResponsiveContainer width="100%" height="100%">
                {chart.type === "bar" ? (
                  <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#303b5a" />
                    <XAxis dataKey="label" stroke="#a9b5cf" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#a9b5cf" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: "#171e3b",
                        border: "1px solid #394868",
                        borderRadius: 10,
                        color: "#f8fafc",
                      }}
                    />
                    <Bar
                      dataKey="value"
                      fill="#20d6f7"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                ) : (
                  <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#303b5a" />
                    <XAxis dataKey="label" stroke="#a9b5cf" tick={{ fontSize: 11 }} />
                    <YAxis stroke="#a9b5cf" tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: "#171e3b",
                        border: "1px solid #394868",
                        borderRadius: 10,
                        color: "#f8fafc",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#20d6f7"
                      strokeWidth={3}
                      dot={{ fill: "#20d6f7", r: 4 }}
                    />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          </article>
        );
      })}

      {report.insights.length > 0 && (
        <section className="analytics-insights">
          <h3>Insights da análise</h3>

          {report.insights.map((insight, index) => (
            <article
              className={`analytics-insight ${insight.type}`}
              key={index}
            >
              <strong>{insight.title}</strong>
              <p>{insight.description}</p>
            </article>
          ))}
        </section>
      )}

      {report.sources.length > 0 && (
        <footer className="analytics-sources">
          <strong>Fontes analisadas:</strong>
          <p>{report.sources.join(", ")}</p>
        </footer>
      )}
    </section>
  );
}
