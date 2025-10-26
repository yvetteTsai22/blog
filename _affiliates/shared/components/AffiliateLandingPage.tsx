import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Check } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

type HighlightStyle = "gradient" | "background" | "underline";

interface Highlight {
  text: string;
  style: HighlightStyle;
}

interface SocialProofItem {
  value: string;
  label: string;
}

interface LandingPageProps {
  headline?: string;
  highlights?: Highlight[]; // Array of phrases to highlight with different styles
  subheadline?: string;
  benefits?: string[];
  ctaText?: string;
  ctaLink?: string;
  productImageUrl?: string;
  socialProof?: SocialProofItem[]; // Array of social proof metrics (leave empty to hide section)
}

export function AffiliateLandingPage({
  headline = "Discover the Secret Tool That's Transforming How Thousands Work Smarter, Not Harder",
  highlights = [
    { text: "Secret Tool", style: "gradient" },
    { text: "Smarter, Not Harder", style: "background" }
  ],
  subheadline = "What if you could reclaim 10+ hours every week without changing your entire workflow? This game-changing solution does exactly that—and it takes just minutes to set up.",
  benefits = [
    "Save over 10 hours per week with intelligent automation",
    "Eliminate repetitive tasks that drain your productivity",
    "Get results in minutes, not days—no learning curve required",
    "Works seamlessly with the tools you already use",
    "Join 50,000+ professionals who've already made the switch"
  ],
  ctaText = "Unlock Instant Access",
  ctaLink = "#your-affiliate-link-here",
  productImageUrl = "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80",
  socialProof = [
    { value: "50,000+", label: "Active Users" },
    { value: "4.9/5", label: "Average Rating" },
    { value: "10+ Hours", label: "Saved Per Week" }
  ]
}: LandingPageProps) {
  
  const handleCTAClick = (e: React.MouseEvent) => {
    // Replace with actual affiliate link
    if (ctaLink === "#your-affiliate-link-here") {
      e.preventDefault();
      console.log("Please add your affiliate link to the ctaLink prop");
    }
  };

  // Function to render a highlighted span based on style
  const renderHighlight = (text: string, style: HighlightStyle, key: number) => {
    switch (style) {
      case "gradient":
        return (
          <span key={key} className="relative inline-block">
            <span className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 blur-lg opacity-30"></span>
            <span className="relative bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {text}
            </span>
          </span>
        );
      case "background":
        return (
          <span key={key} className="relative">
            <span className="bg-amber-200 dark:bg-amber-500/30 px-2 -mx-2 rounded">
              {text}
            </span>
          </span>
        );
      case "underline":
        return (
          <span key={key} className="relative inline-block">
            <span className="absolute bottom-1 left-0 w-full h-3 bg-blue-200 dark:bg-blue-900/50 -z-10"></span>
            <span className="relative">{text}</span>
          </span>
        );
      default:
        return <span key={key}>{text}</span>;
    }
  };

  // Function to render headline with all highlighted phrases
  const renderHeadline = () => {
    if (!highlights || highlights.length === 0) {
      return headline;
    }

    // Create a map of text to style
    const highlightMap = new Map(highlights.map(h => [h.text, h.style]));
    
    // Sort highlights by length (longest first) to avoid partial matches
    const sortedHighlights = [...highlights].sort((a, b) => b.text.length - a.text.length);
    
    // Split the headline by all highlight texts
    let parts: Array<{ text: string; style?: HighlightStyle }> = [{ text: headline }];
    
    sortedHighlights.forEach(highlight => {
      const newParts: Array<{ text: string; style?: HighlightStyle }> = [];
      
      parts.forEach(part => {
        if (part.style) {
          // Already highlighted, keep as is
          newParts.push(part);
        } else if (part.text.includes(highlight.text)) {
          // Split by this highlight
          const segments = part.text.split(highlight.text);
          segments.forEach((segment, index) => {
            if (segment) {
              newParts.push({ text: segment });
            }
            if (index < segments.length - 1) {
              newParts.push({ text: highlight.text, style: highlight.style });
            }
          });
        } else {
          newParts.push(part);
        }
      });
      
      parts = newParts;
    });

    // Render the parts
    return parts.map((part, index) => {
      if (part.style) {
        return renderHighlight(part.text, part.style, index);
      }
      return <span key={index}>{part.text}</span>;
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-12 md:py-24">
        <div className="max-w-6xl mx-auto">
          
          {/* Headline */}
          <h1 className="text-center mb-12 md:mb-16 px-4 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold leading-tight tracking-tight text-slate-900 dark:text-slate-50">
            {renderHeadline()}
          </h1>

          {/* Image and Copy Section - Side by side on desktop */}
          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center mb-16">
            {/* Product Image */}
            <div className="rounded-lg overflow-hidden shadow-2xl">
              <ImageWithFallback 
                src={productImageUrl}
                alt="Product showcase"
                className="w-full h-auto"
              />
            </div>

            {/* Supporting Copy */}
            <div>
              <p className="text-slate-700 dark:text-slate-300 mb-8 text-lg">
                {subheadline}
              </p>

              {/* Benefits List */}
              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      <div className="w-6 h-6 rounded-full bg-green-500/10 flex items-center justify-center">
                        <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                      </div>
                    </div>
                    <span className="text-slate-700 dark:text-slate-300">
                      {benefit}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Social Proof Section */}
          {socialProof && socialProof.length > 0 && (
            <div className="max-w-3xl mx-auto mb-12 text-center px-4">
              <div className={`grid gap-8 ${
                socialProof.length === 1 ? 'grid-cols-1' :
                socialProof.length === 2 ? 'md:grid-cols-2' :
                socialProof.length === 3 ? 'md:grid-cols-3' :
                'md:grid-cols-4'
              }`}>
                {socialProof.map((item, index) => (
                  <div key={index} className="space-y-2">
                    <div className="text-slate-900 dark:text-slate-50">{item.value}</div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom CTA Section */}
          <div className="max-w-2xl mx-auto text-center bg-slate-100 dark:bg-slate-800 rounded-lg p-8 md:p-12">
            <h2 className="mb-4 text-slate-900 dark:text-slate-50">
              Ready to Transform Your Workflow?
            </h2>
            <p className="text-slate-700 dark:text-slate-300 mb-6">
              Join thousands who've already discovered the smarter way to work.
            </p>
            <Button 
              size="lg" 
              className="px-8 py-6 text-lg shadow-xl hover:shadow-2xl transition-shadow"
              asChild
            >
              <a href={ctaLink} onClick={handleCTAClick}>
                {ctaText}
              </a>
            </Button>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-4">
              No credit card required • Instant access • Cancel anytime
            </p>
          </div>

        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-8">
        <div className="container mx-auto px-4">
          <p className="text-center text-sm text-slate-600 dark:text-slate-400">
            © {new Date().getFullYear()} • Affiliate Disclosure: This page contains affiliate links.
          </p>
        </div>
      </footer>
    </div>
  );
}
