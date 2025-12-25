import PageContainer from "@/components/page-contaner";

export default function PrivacyPage() {
  return (
    <PageContainer title="Privacy Policy">
      <div className="space-y-10">
        <section>
          <p className="text-sm text-muted-foreground leading-relaxed">
            DisasterLens is a final year academic project developed for
            educational purposes. We respect user privacy and are transparent
            about the limited data we collect.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Information Collected
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We only collect email addresses. No other personal information is
            collected.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Purpose of Collection
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Email addresses are used solely for notifications or updates related
            to the platform.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Data Storage & Security
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Collected emails are stored securely and are not shared with third
            parties.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">Data Removal</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Users may request removal of their email at any time.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-semibold text-primary">
            Academic Notice
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            This project is for educational purposes only and does not operate
            as a commercial service.
          </p>
        </section>
      </div>
    </PageContainer>
  );
}
