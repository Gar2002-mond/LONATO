/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./gestloto/templates/**/*.html",
    "./**/*.py", // Pour les chaînes contenant des classes Tailwind
  ],
  // theme: {
  //   extend: {
  //     fontFamily: {
  //       sans: [
  //         "Roboto",
  //         "popins",
  //         "system-ui",
  //         "-apple-system",
  //         "BlinkMacSystemFont",
  //         "Segoe UI",
  //         "Roboto",
  //         "Arial",
  //         "sans-serif",
  //       ],
  //     },
  //     //   colors: {
  //     //     primary: {
  //     //       50: "#f0f9ff",
  //     //       100: "#e0f2fe",
  //     //       200: "#bae6fd",
  //     //       300: "#7dd3fc",
  //     //       400: "#38bdf8",
  //     //       500: "#0ea5e9",
  //     //       600: "#0284c7",
  //     //       700: "#0369a1",
  //     //       800: "#075985",
  //     //       900: "#0c4a6e",
  //     //     },
  //     //   },
  //     colors: {
  //       // "custom-primary": "#000000",
  //       "custom-bg-body": "#F8F9FA",
  //       "custom-bg-input": "#F1F3F5",
  //       // "custom-text": "#212529",
  //       // "custom-muted": "#6C757D",
  //     },
  //     borderRadius: {
  //       card: "1rem", // exemple 16px
  //     },
  //   },
  // },
  plugins: [require("@tailwindcss/forms"), require("daisyui")],
  variants: {
    extend: {
      opacity: ["responsive", "hover", "focus", "group-hover"],
      backgroundColor: ["responsive", "hover", "focus", "active"],
      // ...
    },
    daisyui: {
      themes: [
        {
          lonato: {
            primary: "#1c64f2",
            secondary: "#818cf8",
            accent: "#f59e0b",
            neutral: "#2a2e37",
            "base-100": "#ffffff",
            info: "#3abff8",
            success: "#36d399",
            warning: "#fbbd23",
            error: "#f87272",
          },
        },
      ],
    },
  },
};
