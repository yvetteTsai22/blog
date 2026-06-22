import { useEffect } from "react";
import "../instadoodle.css";

interface Props {
  affiliateUrl: string;
  productName?: string;
  price?: string;
  priceNote?: string;
  userCount?: string;
  rating?: string;
  guarantee?: string;
}

export function InstadoodleLandingPage({
  affiliateUrl,
  price = "$37",
  priceNote = "one-time payment — no monthly fees",
  userCount = "90,000+",
  rating = "4.9",
  guarantee = "60",
}: Props) {
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("in"); });
      },
      { threshold: 0.12 }
    );
    document.querySelectorAll(".fu").forEach((el) => obs.observe(el));

    const staggerObs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const kids = e.target.querySelectorAll<HTMLElement>(":scope > *");
          kids.forEach((c, i) => {
            c.style.opacity = "0";
            c.style.transform = "translateY(22px)";
            c.style.transition = `opacity .45s ${i * 0.1}s ease, transform .45s ${i * 0.1}s ease`;
            setTimeout(() => { c.style.opacity = "1"; c.style.transform = "translateY(0)"; }, 60);
          });
          staggerObs.unobserve(e.target);
        });
      },
      { threshold: 0.08 }
    );
    document.querySelectorAll(".stagger").forEach((el) => staggerObs.observe(el));

    return () => { obs.disconnect(); staggerObs.disconnect(); };
  }, []);

  return (
    <>
      {/* NAV */}
      <nav className="nav">
        <div className="wrap nav-row">
          <a href="#" className="logo" aria-label="InstaDoodle home">insta<b>doodle</b></a>
          <a href={affiliateUrl} className="nav-btn" target="_blank" rel="noopener noreferrer">
            Start Creating →
          </a>
        </div>
      </nav>

      {/* HERO */}
      <header className="hero">
        <div className="hero-dots" aria-hidden="true" />
        <div className="wrap">
          <div className="hero-grid">
            <div>
              <p className="hero-eye">AI-Powered Whiteboard Video Creator</p>
              <h1 className="hero-h1">
                <span className="l1">WHITEBOARD</span>
                <span className="l2">VIDEOS THAT</span>
                <span className="l3">CONVERT.</span>
              </h1>
              <p className="hero-sub">
                Type a description, click Generate — and InstaDoodle's DoodleAI™ engine turns your idea into a professional whiteboard animation in minutes. No drawing. No software. No monthly fee.
              </p>
              <div className="cta-row">
                <a href={affiliateUrl} className="btn-main pulse" target="_blank" rel="noopener noreferrer">
                  Get InstaDoodle Now ✦
                </a>
                <a href="#how" className="btn-ghost">See how it works</a>
              </div>
              <div className="soc-proof">
                <span className="gold">★★★★★</span>
                <span>Trusted by {userCount} business owners worldwide</span>
              </div>
            </div>

            <div className="mockup-wrap">
              <div className="mockup">
                <div className="mockup-bar">
                  <div className="dot" />
                  <div className="dot" />
                  <div className="dot" />
                  <span className="mockup-label">explainer-video.instadoodle</span>
                </div>
                <div className="mockup-canvas">
                  <svg
                    viewBox="0 0 280 180"
                    xmlns="http://www.w3.org/2000/svg"
                    style={{ maxWidth: 280, width: "100%" }}
                    role="img"
                    aria-label="Example doodle animation frame — a whiteboard character scene"
                  >
                    {/* Whiteboard BG hint */}
                    <rect x="20" y="10" width="240" height="160" rx="3" fill="none" stroke="#F0EFE2" strokeWidth="1.5" />
                    {/* Cartoon presenter character */}
                    {/* Body */}
                    <ellipse cx="80" cy="125" rx="22" ry="28" fill="none" stroke="#1E1B14" strokeWidth="2.2" />
                    {/* Head */}
                    <circle cx="80" cy="72" r="22" fill="#FEFDE8" stroke="#1E1B14" strokeWidth="2.2" />
                    {/* Eyes */}
                    <circle cx="73" cy="68" r="3.5" fill="#1E1B14" />
                    <circle cx="87" cy="68" r="3.5" fill="#1E1B14" />
                    <circle cx="74.5" cy="66.5" r="1.2" fill="#fff" />
                    <circle cx="88.5" cy="66.5" r="1.2" fill="#fff" />
                    {/* Smile */}
                    <path d="M72 77 Q80 85 88 77" fill="none" stroke="#1E1B14" strokeWidth="2" strokeLinecap="round" />
                    {/* Neck */}
                    <line x1="80" y1="94" x2="80" y2="97" stroke="#1E1B14" strokeWidth="2.2" />
                    {/* Arms */}
                    <path d="M58 110 Q46 100 42 88" fill="none" stroke="#1E1B14" strokeWidth="2.2" strokeLinecap="round" />
                    <path d="M102 110 Q118 98 128 90" fill="none" stroke="#1E1B14" strokeWidth="2.2" strokeLinecap="round" />
                    {/* Pointing hand */}
                    <circle cx="130" cy="88" r="6" fill="none" stroke="#1E1B14" strokeWidth="2" />
                    <line x1="136" y1="85" x2="145" y2="78" stroke="#1E1B14" strokeWidth="2" strokeLinecap="round" />
                    {/* Legs */}
                    <path d="M68 152 Q64 162 60 170" fill="none" stroke="#1E1B14" strokeWidth="2.2" strokeLinecap="round" />
                    <path d="M92 152 Q96 162 100 170" fill="none" stroke="#1E1B14" strokeWidth="2.2" strokeLinecap="round" />
                    {/* Speech bubble */}
                    <ellipse cx="200" cy="80" rx="62" ry="38" fill="#fff" stroke="#2C5FFF" strokeWidth="2.5" />
                    <path d="M148 90 L140 105 L158 96" fill="#fff" stroke="#2C5FFF" strokeWidth="2.5" strokeLinejoin="round" />
                    <text x="200" y="70" textAnchor="middle" fontFamily="Impact, sans-serif" fontSize="13" fill="#2C5FFF">OUR PRODUCT</text>
                    <text x="200" y="87" textAnchor="middle" fontFamily="Impact, sans-serif" fontSize="13" fill="#FF5C1A">SAVES YOU</text>
                    <text x="200" y="104" textAnchor="middle" fontFamily="Impact, sans-serif" fontSize="13" fill="#1E1B14">TIME + MONEY</text>
                    {/* Decorative doodle stars */}
                    <path d="M230 148 L231.5 143 L233 148 L238 149.5 L233 151 L231.5 156 L230 151 L225 149.5Z" fill="#FF5C1A" />
                    <path d="M42 30 L43.5 25 L45 30 L50 31.5 L45 33 L43.5 38 L42 33 L37 31.5Z" fill="#2C5FFF" />
                    {/* Squiggle underline */}
                    <path d="M155 118 Q162 114 169 118 Q176 122 183 118 Q190 114 197 118" fill="none" stroke="#2C5FFF" strokeWidth="1.5" strokeLinecap="round" />
                    {/* Dots */}
                    <circle cx="240" cy="30" r="3" fill="#FF5C1A" />
                    <circle cx="248" cy="38" r="2" fill="#2C5FFF" />
                    <circle cx="35" cy="150" r="3" fill="#2C5FFF" />
                    <circle cx="27" cy="158" r="2" fill="#FF5C1A" />
                  </svg>
                </div>
                <div className="mockup-prompt">
                  <span className="ptxt">"<em>a friendly presenter explaining our product benefits</em>"</span>
                  <span className="gen-btn">GENERATE</span>
                </div>
              </div>
              <div className="sticker s-ai">⚡ DoodleAI™</div>
              <div className="sticker s-vid">✓ Exports HD Video</div>
            </div>
          </div>
        </div>
      </header>

      {/* TRUST BAR */}
      <div className="trust" role="complementary" aria-label="Trust indicators">
        <div className="wrap">
          <ul className="t-list">
            <li className="t-item"><span className="t-num">{userCount}</span><span className="t-lbl">Business Owners</span></li>
            <li className="t-sep" aria-hidden="true" />
            <li className="t-item"><span className="t-num">{rating}★</span><span className="t-lbl">Average Rating</span></li>
            <li className="t-sep" aria-hidden="true" />
            <li className="t-item"><span className="t-num">{price}</span><span className="t-lbl">One-Time Payment</span></li>
            <li className="t-sep" aria-hidden="true" />
            <li className="t-item"><span className="t-num">{guarantee}-Day</span><span className="t-lbl">Money-Back Guarantee</span></li>
          </ul>
        </div>
      </div>

      {/* PROBLEM / SOLUTION */}
      <section className="prob">
        <div className="wrap">
          <div className="prob-grid">
            <div>
              <p className="eye" style={{ color: "var(--orange)" }}>Sound familiar?</p>
              <p className="prob-quote">
                You have a product worth selling — but nobody <strong>watches your videos.</strong>
              </p>
              <ul className="prob-list">
                <li className="prob-li">Hiring a video agency costs $2,000–$5,000 per explainer — and takes weeks</li>
                <li className="prob-li">DIY animation software has a brutal learning curve and a monthly subscription</li>
                <li className="prob-li">Generic stock animations look like everyone else's content — zero differentiation</li>
                <li className="prob-li">Text-only pages convert poorly; people want to see your idea come to life</li>
                <li className="prob-li">Every hour you spend on production is an hour not spent growing your business</li>
              </ul>
            </div>
            <div className="sol-card">
              <h3>MEET INSTADOODLE.</h3>
              <p>
                The cloud-based whiteboard animation tool that turns a text prompt into a hand-drawn style explainer video — complete with voiceover, music, and HD export. Open a browser, type your idea, and your video is ready before you finish your coffee.
              </p>
              <div className="sol-checks">
                <div className="sc">DoodleAI™ generates scenes from plain text</div>
                <div className="sc">1,000+ doodle characters and elements</div>
                <div className="sc">Built-in voiceover in 40+ languages</div>
                <div className="sc">Commercial license included</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features">
        <div className="wrap">
          <p className="eye fu">What you get</p>
          <h2 className="sh2 fu d1">EVERYTHING YOUR<br />VIDEOS NEED.</h2>
          <p className="ssub fu d2">
            One platform built for marketers, educators, and creators who need professional animated video without a professional budget.
          </p>
          <div className="feat-grid stagger">
            <div className="feat-card">
              <div className="feat-ico">🤖</div>
              <h3 className="feat-title">DoodleAI™ Engine</h3>
              <p className="feat-desc">Type a description and the AI generates a matching doodle character or scene. No clip-art hunting — your exact concept drawn on demand, in seconds.</p>
            </div>
            <div className="feat-card">
              <div className="feat-ico">📚</div>
              <h3 className="feat-title">1,000+ Element Library</h3>
              <p className="feat-desc">A searchable library of doodle characters, arrows, props, speech bubbles, and backgrounds ready to drag into your video. Every style, every industry.</p>
            </div>
            <div className="feat-card">
              <div className="feat-ico">🎙️</div>
              <h3 className="feat-title">AI Voiceover in 40+ Languages</h3>
              <p className="feat-desc">Add a professional voiceover without recording anything. Pick a voice, generate from your script, and InstaDoodle syncs audio to your animation automatically.</p>
            </div>
            <div className="feat-card">
              <div className="feat-ico">📤</div>
              <h3 className="feat-title">1080p HD Export</h3>
              <p className="feat-desc">Download your finished video in 1080p HD — ready for YouTube, landing pages, sales funnels, or social media. No watermarks, no compression, no fuss.</p>
            </div>
            <div className="feat-card">
              <div className="feat-ico">☁️</div>
              <h3 className="feat-title">100% Cloud-Based</h3>
              <p className="feat-desc">Nothing to download or install. Open any browser on any device and your full project history is right there. Works on Mac, Windows, tablet, and more.</p>
            </div>
            <div className="feat-card">
              <div className="feat-ico">📄</div>
              <h3 className="feat-title">Full Commercial License</h3>
              <p className="feat-desc">Every video you create is yours to monetize. Use it in client work, sell it, run ads with it — the license covers all commercial applications with no royalties.</p>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="wrap">
          <p className="eye fu">From idea to video in three steps</p>
          <h2 className="sh2 fu d1">SIMPLE ENOUGH TO<br />START TODAY.</h2>
          <p className="ssub fu d2">No tutorial. No onboarding call. Open InstaDoodle and your first video is generating within the first minute.</p>
          <div className="steps fu d3">
            <div className="step">
              <span className="step-num">01</span>
              <h3 className="step-title">WRITE YOUR SCRIPT</h3>
              <p className="step-desc">Type what you want to explain — or use the AI script generator to turn a topic into a polished outline. Plain language works perfectly.</p>
            </div>
            <div className="step">
              <span className="step-num">02</span>
              <h3 className="step-title">AI DRAWS YOUR SCENES</h3>
              <p className="step-desc">DoodleAI™ generates matching doodle characters and elements for each scene. Pick from the variations, tweak colors and style, add voiceover.</p>
            </div>
            <div className="step">
              <span className="step-num">03</span>
              <h3 className="step-title">EXPORT &amp; PUBLISH</h3>
              <p className="step-desc">Download your HD video in minutes and post it anywhere — your sales page, YouTube channel, Instagram, or email campaign. Done.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FOR WHO */}
      <section>
        <div className="wrap">
          <p className="eye fu">Perfect for</p>
          <h2 className="sh2 fu d1">BUILT FOR PEOPLE<br />WHO SELL IDEAS.</h2>
          <p className="ssub fu d2" style={{ marginBottom: 0 }}>
            Whether you're running a funnel, teaching a course, or pitching a product — InstaDoodle was designed to fit your workflow.
          </p>
          <div className="who-tags fu d3">
            {[
              ["Online Marketers", true],
              ["Course Creators", false],
              ["YouTube Creators", false],
              ["Small Business Owners", false],
              ["Coaches &amp; Consultants", false],
              ["E-commerce Sellers", false],
              ["Educators &amp; Trainers", false],
              ["Agency Owners", false],
              ["Affiliate Marketers", false],
              ["Social Media Managers", false],
            ].map(([label, hi]) => (
              <span
                key={label as string}
                className={`who-tag${hi ? " hi" : ""}`}
                dangerouslySetInnerHTML={{ __html: label as string }}
              />
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section>
        <div className="wrap">
          <p className="eye fu">Real results</p>
          <h2 className="sh2 fu d1">MARKETERS WHO SWITCHED.</h2>
          <p className="ssub fu d2">Not influencers. Real business owners who needed video content and found a better way to produce it.</p>
          <div className="testi-grid stagger">
            <div className="tc">
              <div className="tc-stars">★★★★★</div>
              <p className="tc-text">"I was paying a freelancer $800 per video for my sales funnel. InstaDoodle paid for itself on the first video I made in-house. The DoodleAI scenes are actually better — I can change them in 30 seconds if my copy changes."</p>
              <div className="tc-auth">
                <div className="tc-av">R</div>
                <div>
                  <div className="tc-name">Rachel M.</div>
                  <div className="tc-role">Online marketer · Austin TX</div>
                </div>
              </div>
            </div>
            <div className="tc">
              <div className="tc-stars">★★★★★</div>
              <p className="tc-text">"I run a Shopify store and added an InstaDoodle explainer to every product page. My add-to-cart rate went up 34% in two weeks. I can't explain it better than that — just go try it."</p>
              <div className="tc-auth">
                <div className="tc-av">K</div>
                <div>
                  <div className="tc-name">Kevin L.</div>
                  <div className="tc-role">E-commerce store owner · 8K monthly orders</div>
                </div>
              </div>
            </div>
            <div className="tc">
              <div className="tc-stars">★★★★★</div>
              <p className="tc-text">"I teach online courses and used to outsource all my intro videos. Now I make them myself the morning I need them. The multilingual voiceover alone made it worth it — I expanded into Spanish-speaking markets without hiring anyone."</p>
              <div className="tc-auth">
                <div className="tc-av">S</div>
                <div>
                  <div className="tc-name">Sofia D.</div>
                  <div className="tc-role">Course creator · 4,200 enrolled students</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* GUARANTEE */}
      <section className="guar">
        <div className="wrap">
          <div className="guar-row">
            <div>
              <div className="guar-badge" aria-label={`${guarantee}-day money-back guarantee`}>
                <span className="gd">{guarantee}</span>
                <span className="gl">Day</span>
                <span className="gw">Money Back</span>
              </div>
            </div>
            <div className="guar-text">
              <h3>TRY IT RISK-FREE.</h3>
              <p>
                Create whiteboard videos for {guarantee} full days. If InstaDoodle doesn't save you time, improve your conversion rates, and pay for itself several times over — email support and get a full refund, no questions asked. The guarantee exists because this works, and we're willing to put {price} on it.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="final" id="get">
        <div className="final-dots" aria-hidden="true" />
        <div className="wrap">
          <h2>
            YOUR NEXT VIDEO IS<br />
            <span className="clr">ONE CLICK AWAY.</span>
          </h2>
          <p className="final-sub">
            Stop waiting for freelancers. Stop paying for subscriptions. Start shipping explainer videos that actually move people — today, for {price}.
          </p>
          <div className="price-badge">
            <span className="price-big">{price}</span>
            <div>
              <div className="price-note">{priceNote}</div>
              <div className="price-vs">vs. $39/month with competitors</div>
            </div>
          </div>
          <div className="final-cta-wrap">
            <a
              href={affiliateUrl}
              className="btn-main pulse"
              style={{ fontSize: "1.1rem", padding: "18px 36px" }}
              target="_blank"
              rel="noopener noreferrer"
            >
              Get InstaDoodle Today →
            </a>
          </div>
          <p className="final-note">{guarantee}-day money-back guarantee · Commercial license included · Instant browser access</p>
        </div>
      </section>

      {/* FAQ */}
      <section className="faq">
        <div className="wrap">
          <p className="eye">Common questions</p>
          <h2 className="sh2" style={{ marginBottom: 40 }}>QUICK ANSWERS.</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <p className="faq-q">Do I need any video or design experience?</p>
              <p className="faq-a">None at all. If you can type a sentence, you can produce a video with InstaDoodle. The AI handles every visual decision — characters, composition, style. You guide the story; it builds the frames.</p>
            </div>
            <div className="faq-item">
              <p className="faq-q">What makes this different from Doodly or VideoScribe?</p>
              <p className="faq-a">InstaDoodle charges {price} once — not $39 every month. More importantly, the DoodleAI™ engine lets you generate custom scenes from text prompts, which older tools simply can't do. You describe exactly what you want; it draws it.</p>
            </div>
            <div className="faq-item">
              <p className="faq-q">Can I use the videos commercially — for clients, ads, products?</p>
              <p className="faq-a">Yes, full commercial rights included. Use your videos in client deliverables, paid ad campaigns, sales funnels, YouTube channels, or digital products. No royalties, no attribution required.</p>
            </div>
            <div className="faq-item">
              <p className="faq-q">What if it doesn't work for me?</p>
              <p className="faq-a">The {guarantee}-day guarantee makes the downside exactly {price}. Use InstaDoodle for two full months — create real videos and test them. If you're not satisfied, request a refund through ClickBank and receive it immediately, no conditions attached.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="wrap foot-row">
          <a href="#" className="foot-logo">insta<b>doodle</b></a>
          <div className="foot-links">
            <a href={affiliateUrl} target="_blank" rel="noopener noreferrer">Get Access</a>
            <a href="#features">Features</a>
            <a href="#how">How It Works</a>
            <a href="#get">Pricing</a>
          </div>
          <p className="foot-copy">© {new Date().getFullYear()} InstaDoodle. All rights reserved.</p>
        </div>
      </footer>
      <div className="disc">
        <div className="wrap">
          <p>This page contains affiliate links. If you purchase through these links, we may earn a commission at no additional cost to you. We only recommend products we believe deliver genuine value.</p>
        </div>
      </div>
    </>
  );
}
