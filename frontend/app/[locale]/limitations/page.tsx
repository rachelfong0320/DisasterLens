import PageContainer from "@/components/page-contaner";

export default function LimitationsPage() {
  return (
    <PageContainer title="Limitations & Accuracy">
      <h2>Not an Emergency Service</h2>
      <p>
        DisasterLens is an informational platform only and does not provide
        official emergency alerts or instructions.
      </p>

      <h2>Data Accuracy</h2>
      <p>
        Disaster-related data may be delayed, incomplete, inaccurate, or revised
        after publication.
      </p>

      <h2>Coverage Gaps</h2>
      <p>
        Some regions or disaster types may have limited or inconsistent data
        coverage.
      </p>

      <h2>Interpretation Risk</h2>
      <p>
        Visualizations and summaries are intended for awareness only and should
        not be used for critical decision-making.
      </p>

      <h2>Technical Limitations</h2>
      <p>
        System performance may be affected by API downtime, rate limits, or
        processing delays.
      </p>

      <h2>Continuous Improvement</h2>
      <p>
        We continuously improve data quality, processing logic, and coverage
        based on feedback and testing.
      </p>
    </PageContainer>
  );
}
