const research = [
  {
    number: "01",
    title: "Nepali language intelligence",
    description:
      "Evaluate language understanding across Nepali, Romanized Nepali and code-switched conversations.",
    tag: "LANGUAGE SYSTEMS",
  },
  {
    number: "02",
    title: "Reliable knowledge AI",
    description:
      "Build systems that retrieve evidence, cite source material and acknowledge when information is missing.",
    tag: "TRUST & EVALUATION",
  },
  {
    number: "03",
    title: "Efficient AI systems",
    description:
      "Explore model routing, inference efficiency and practical AI that remains affordable to operate.",
    tag: "APPLIED RESEARCH",
  },
];

const principles = [
  ["Evidence over hype", "We measure performance and publish limitations."],
  ["Privacy by design", "Customer information is protected and access is controlled."],
  ["Human-directed systems", "Sensitive actions require clear authorization."],
];

export default function HomePage() {
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="NIL.ai home">
          <span className="mark">N</span>
          <span>NIL<span className="accent">.ai</span></span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#mission">Mission</a>
          <a href="#research">Research</a>
          <a href="#products">Products</a>
          <a href="#principles">Principles</a>
        </nav>
        <a className="header-cta" href="https://github.com/gamer631/np-ai">
          Explore GitHub <span aria-hidden="true">↗</span>
        </a>
      </header>

      <main id="main-content">
      <section className="hero" id="top">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-copy">
          <p className="eyebrow"><span className="status-dot" /> INDEPENDENT AI RESEARCH & ENGINEERING</p>
          <h1>Born in Nepal.<br /><span>Built for the world.</span></h1>
          <p className="hero-lede">
            Nepal Innovation Labs researches and engineers useful, reliable
            artificial intelligence for people and organizations everywhere.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#products">Explore our work <span aria-hidden="true">↗</span></a>
            <a className="button button-quiet" href="#research">Our research</a>
          </div>
          <div className="hero-footnote">
            <span>NEPAL ROOTED</span><i /> <span>GLOBALLY MINDED</span><i /> <span>RESEARCH LED</span>
          </div>
        </div>
        <div className="orbital" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit orbit-three" />
          <div className="core"><span>N</span><small>NIL CORE</small></div>
          <span className="node node-a">LANGUAGE</span>
          <span className="node node-b">REASONING</span>
          <span className="node node-c">RELIABILITY</span>
          <span className="crosshair crosshair-a">+</span>
          <span className="crosshair crosshair-b">+</span>
        </div>
        <div className="hero-index"><span>01</span> / 04</div>
      </section>

      <section className="ticker" aria-label="Our focus areas">
        <span>AI RESEARCH</span><b>✳</b><span>PRODUCT ENGINEERING</span><b>✳</b><span>NEPALI LANGUAGE TECHNOLOGY</span><b>✳</b><span>RESPONSIBLE INNOVATION</span>
      </section>

      <section className="section mission" id="mission">
        <div className="section-label"><span>01</span> / THE MISSION</div>
        <div>
          <p className="kicker">A LABORATORY FOR USEFUL IDEAS</p>
          <h2>Technology should move<br /> <em>everyone</em> forward.</h2>
          <p className="section-copy">
            We are building a Nepal-born technology company with a research
            mindset: understand the problem, test the idea, engineer the
            solution and share what we learn.
          </p>
        </div>
        <div className="mission-stamp"><span>RESEARCH</span><b>×</b><span>ENGINEERING</span><b>×</b><span>IMPACT</span></div>
      </section>

      <section className="section research" id="research">
        <div className="section-heading">
          <div className="section-label"><span>02</span> / RESEARCH DIRECTIONS</div>
          <p className="kicker">QUESTIONS WORTH ENGINEERING</p>
          <h2>Build from<br /><em>first principles.</em></h2>
        </div>
        <div className="research-list">
          {research.map((item) => (
            <article className="research-card" key={item.number}>
              <span className="research-number">{item.number}</span>
              <div><p className="card-tag">{item.tag}</p><h3>{item.title}</h3><p>{item.description}</p></div>
              <span className="card-arrow" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
      </section>

      <section className="product-band" id="products">
        <div className="product-visual" aria-hidden="true">
          <div className="window-bar"><i /><i /><i /><span>NP.AI / KNOWLEDGE WORKSPACE</span></div>
          <div className="mock-line short" /><div className="mock-line" /><div className="mock-line medium" />
          <div className="mock-answer"><span>ANSWER / SOURCE VERIFIED</span><b>Knowledge, connected.</b><i /><i /><i /></div>
          <div className="mock-chip">SOURCE 01 · POLICY.PDF</div>
        </div>
        <div className="product-copy">
          <div className="section-label"><span>03</span> / FLAGSHIP PRODUCT</div>
          <p className="kicker">MADE AT NIL.AI</p>
          <h2>Meet <em>NP.ai</em></h2>
          <p>
            A multilingual AI workspace designed to help teams understand
            their own documents, find evidence and complete approved work.
          </p>
          <ul><li>Grounded document answers</li><li>Nepali + English workflows</li><li>Privacy-aware organization workspaces</li></ul>
          <a className="text-link" href="https://github.com/gamer631/np-ai">Explore the open-source project <span aria-hidden="true">↗</span></a>
          <small className="disclaimer">Product capabilities are under active development; availability and readiness are not implied.</small>
        </div>
      </section>

      <section className="section principles" id="principles">
        <div className="section-label"><span>04</span> / HOW WE WORK</div>
        <div className="principle-intro"><p className="kicker">TRUST IS AN ENGINEERING REQUIREMENT</p><h2>Ambition,<br /><em>with discipline.</em></h2></div>
        <div className="principle-list">
          {principles.map(([title, description], index) => (
            <article key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{description}</p></div></article>
          ))}
        </div>
      </section>

      </main>

      <footer className="footer" aria-label="Site footer">
        <div className="footer-top"><a className="wordmark" href="#top"><span className="mark">N</span><span>NIL<span className="accent">.ai</span></span></a><p>Intelligence. Innovation. Engineering.</p></div>
        <div className="footer-bottom"><span>© {new Date().getFullYear()} Nepal Innovation Labs. Working identity.</span><a href="https://github.com/gamer631/np-ai">GitHub ↗</a><span>Born in Nepal. Built for the world.</span></div>
      </footer>
    </>
  );
}
