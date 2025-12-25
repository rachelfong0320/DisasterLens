import PageContainer from "@/components/page-contaner";

export default function LimitationsPage() {
  return (
    <PageContainer title="Limitations & Accuracy">
      <div className="space-y-8">
        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Not an Emergency Service
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens is an informational platform only and does not provide
            official emergency alerts or instructions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Data Accuracy
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Disaster-related data may be delayed, incomplete, inaccurate, or
            revised after publication.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Coverage Gaps
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Some regions or disaster types may have limited or inconsistent data
            coverage.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Interpretation Risk
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Visualizations and summaries are intended for awareness only and
            should not be used for critical decision-making.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Technical Limitations
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            System performance may be affected by API downtime, rate limits, or
            processing delays.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Continuous Improvement
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We continuously improve data quality, processing logic, and coverage
            based on feedback and testing.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
