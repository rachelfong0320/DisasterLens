import PageContainer from "@/components/page-contaner";

const team = [
  {
    name: "Rachel Fong Tong Wen",
    role: "Co-Founder / Developer",
    linkedin: "https://www.linkedin.com/in/rachel-fong-tong-wen-4b0329301/",
  },
  {
    name: "Ng Yong Jing",
    role: "Co-Founder / Developer",
    linkedin: "https://www.linkedin.com/in/yong-jing-ng/",
  },
];

export default function TeamPage() {
  return (
    <PageContainer title="Our Team">
      <p className="mb-10">
        DisasterLens is developed and maintained by a small independent team.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {team.map((member) => (
          <div
            key={member.name}
            className="rounded-lg border border-border bg-card p-6"
          >
            <h3 className="font-semibold text-lg">{member.name}</h3>
            <p className="text-sm text-muted-foreground mb-3">{member.role}</p>
            <a
              href={member.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              LinkedIn →
            </a>
          </div>
        ))}
      </div>
    </PageContainer>
  );
}
