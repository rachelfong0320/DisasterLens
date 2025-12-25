export default function Footer() {
  return (
    <footer className="w-full border-t border-border bg-card px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between gap-8 mb-10">
        {/* Left: Brand */}
        <div className="md:w-1/3">
          <h3 className="font-bold text-2xl text-primary mb-3">DisasterLens</h3>
          <p className="text-sm text-muted-foreground">
            Real-time disaster tracking and analysis for Malaysia.
          </p>
        </div>

        {/* Right: Links */}
        <div className="md:w-2/3 grid grid-cols-1 sm:grid-cols-3 gap-8">
          {/* Transparency */}
          <div>
            <h4 className="font-semibold mb-4">Transparency</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="/methodology"
                  className="text-muted-foreground hover:text-foreground"
                >
                  How Our Data Works
                </a>
              </li>
              <li>
                <a
                  href="/data-sources"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Data Sources
                </a>
              </li>
              <li>
                <a
                  href="/limitations"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Limitations
                </a>
              </li>
            </ul>
          </div>

          {/* Project */}
          <div>
            <h4 className="font-semibold mb-4">Project</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://github.com/rachelfong0320/DisasterLens"
                  className="text-muted-foreground hover:text-foreground"
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="/team"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Developers
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="/privacy"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Privacy Policy
                </a>
              </li>
              <li>
                <a
                  href="/term"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Terms of Use
                </a>
              </li>
              <li>
                <a
                  href="/disclaimer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Disclaimer
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-border pt-6 max-w-7xl mx-auto">
        <p className="text-sm text-muted-foreground text-center md:text-left">
          © 2025 DisasterLens. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
