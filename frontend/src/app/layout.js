import { Archivo, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { AppProvider } from "@/context/AppContext";
import Navbar from "@/components/Navbar";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-ibm-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata = {
  title: "Nagarik - Community Hero Civic Portal",
  description: "Report local issues, track resolution, earn points, and make your community a better place.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${archivo.variable} ${ibmPlexSans.variable} ${ibmPlexMono.variable}`}>
      <body>
        <AppProvider>
          <Navbar />
          <main style={{ minHeight: "calc(100vh - 64px)", display: "flex", flexDirection: "column", paddingTop: "88px" }}>
            {children}
          </main>
        </AppProvider>
      </body>
    </html>
  );
}
