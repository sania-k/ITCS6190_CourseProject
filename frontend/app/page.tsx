import { Header } from "@/components/header"
import { HeroSection } from "@/components/hero-section"
import { FlightPredictor } from "@/components/flight-predictor"
import { RouteVisualizations } from "@/components/route-visualizations"
import { AboutSection } from "@/components/about-section"
import { ChillZone } from "@/components/chill-zone"

export default function Home() {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <FlightPredictor />
        <AboutSection />
      </main>
      <footer className="border-t bg-card py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© 2025 SkyWatch CLT. Predicting delays with precision.</p>
        </div>
      </footer>
    </div>
  )
}
