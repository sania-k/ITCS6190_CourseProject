"use client"

import { Plane } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Header() {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    element?.scrollIntoView({ behavior: "smooth" })
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <Plane className="h-6 w-6 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold leading-none text-foreground">SkyWatch</span>
            <span className="text-xs text-muted-foreground">CLT Airport</span>
          </div>
        </div>

        <nav className="hidden gap-1 md:flex">
          <Button variant="ghost" onClick={() => scrollToSection("predictor")}>
            Predictor
          </Button>
          <Button variant="ghost" onClick={() => scrollToSection("routes")}>
            Route Map
          </Button>
          <Button variant="ghost" onClick={() => scrollToSection("about")}>
            About
          </Button>
          <Button variant="ghost" onClick={() => scrollToSection("chill-zone")}>
            Chill Zone
          </Button>
        </nav>
      </div>
    </header>
  )
}
