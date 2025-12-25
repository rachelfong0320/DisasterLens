import PageContainer from "@/components/page-contaner";

export default function DisclaimerPage() {
  return (
    <PageContainer title="Academic Disclaimer">
      <div className="space-y-8">
        <section>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens is a <strong>final year academic project</strong>{" "}
            developed for educational purposes. It is{" "}
            <strong>not an official emergency service</strong> and is{" "}
            <strong>not affiliated with any government agency</strong>.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Not for Emergency Use
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Information provided should <strong>not</strong> be relied upon for
            emergency response. Always consult official government channels for
            disaster guidance.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">
            Data Limitations
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Data may be delayed, incomplete, inaccurate, or subject to change.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-primary mb-2">Liability</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Use of the platform is at the user’s own risk. DisasterLens takes no
            responsibility for decisions made based on this data.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
