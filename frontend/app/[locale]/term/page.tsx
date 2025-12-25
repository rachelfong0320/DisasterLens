import PageContainer from "@/components/page-contaner";

export default function TermsPage() {
  return (
    <PageContainer title="Terms of Use">
      <div className="space-y-10">
        <section>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens is a final year academic project intended for learning
            and demonstration purposes only.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">Platform Use</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Users understand that the information provided is for general
            awareness and demonstration only. The system may contain errors,
            delays, or incomplete data.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">No Guarantees</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We do not guarantee data accuracy, completeness, or availability of
            the service.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Third-Party Data
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Some data comes from third-party providers. DisasterLens does not
            modify or control the original content.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Platform Changes
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            The platform may be updated, modified, or discontinued at any time
            as part of academic development.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
