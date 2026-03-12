import './globals.css';

export const metadata = {
  title: 'Credpanion — Agentic Credit Intelligence Platform',
  description: 'Multi-agent AI credit committee simulation for corporate loan evaluation',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
