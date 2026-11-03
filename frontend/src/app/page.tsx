import { ExamplesGallery } from "@/components/landing/ExamplesGallery";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { WhatsNew } from "@/components/landing/WhatsNew";

export default function HomePage() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <ExamplesGallery />
      <WhatsNew />
    </>
  );
}
