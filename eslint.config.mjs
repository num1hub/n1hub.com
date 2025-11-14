import js from "@eslint/js";
import tseslint from "typescript-eslint";
import nextPlugin from "@next/eslint-plugin-next";
import globals from "globals";

const ignores = [
  "**/*.cjs",
  "**/*.mjs",
  "**/*.json",
  "**/*.d.ts",
  "**/*.py",
  "**/*.pyi",
  "node_modules/**",
  ".next/**",
  "apps/engine/**",
  "dist/**",
  "build/**",
  "coverage/**",
];

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores,
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@next/next": nextPlugin,
    },
    settings: {
      next: {
        rootDir: ["./"],
      },
    },
    rules: {
      "@next/next/no-html-link-for-pages": "off",
    },
  },
  {
    files: ["__tests__/**/*.{ts,tsx}", "**/*.test.{ts,tsx}"],
    languageOptions: {
      globals: {
        ...globals.vitest,
      },
    },
  }
);
