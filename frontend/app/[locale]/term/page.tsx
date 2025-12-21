import PageContainer from "@/components/page-contaner";

export default function TermsPage() {
  return (
    <PageContainer title="Terms of Use">
      <p>
        DisasterLens is a final year academic project intended for learning and
        demonstration purposes only.
      </p>

      <h2>Platform Use</h2>
      <p>
        Users understand that the information provided is for general awareness
        and demonstration only. The system may contain errors, delays, or
        incomplete data.
      </p>

      <h2>No Guarantees</h2>
      <p>
        We do not guarantee data accuracy, completeness, or availability of the
        service.
      </p>

      <h2>Third-Party Data</h2>
      <p>
        Some data comes from third-party providers. DisasterLens does not modify
        or control the original content.
      </p>

      <h2>Platform Changes</h2>
      <p>
        The platform may be updated, modified, or discontinued at any time as
        part of academic development.
      </p>
    </PageContainer>
  );
}
