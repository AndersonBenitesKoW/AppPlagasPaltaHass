// @ts-check
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import boundaries from 'eslint-plugin-boundaries';

const elements = [
  {
    type: 'app',
    pattern: ['src/app/**', 'src/main.tsx', 'src/index.css', 'src/*.tsx'],
    mode: 'full',
  },
  { type: 'core', pattern: 'src/core/**', mode: 'full' },
  { type: 'shared', pattern: 'src/shared/**', mode: 'full' },
  { type: 'features', pattern: 'src/features/**', mode: 'folder', capture: ['feature'] },
  { type: 'test', pattern: 'src/test/**', mode: 'full' },
];

export default tseslint.config(
  {
    ignores: [
      'dist',
      'node_modules',
      'coverage',
      'playwright-report',
      'test-results',
      'src/core/http/schema.d.ts',
    ],
  },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: {
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        File: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        Headers: 'readonly',
        Request: 'readonly',
        Response: 'readonly',
        crypto: 'readonly',
        process: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        queueMicrotask: 'readonly',
        structuredClone: 'readonly',
        AbortController: 'readonly',
        AbortSignal: 'readonly',
        ReadableStream: 'readonly',
        WritableStream: 'readonly',
        TransformStream: 'readonly',
        HTMLElement: 'readonly',
        HTMLInputElement: 'readonly',
        HTMLFormElement: 'readonly',
        Event: 'readonly',
        CustomEvent: 'readonly',
        location: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
      },
    },
    settings: {
      react: { version: '19.0' },
      'boundaries/ignore': ['**/*.css', '**/*.d.ts', '**/*.svg', '**/*.json'],
      'import/resolver': {
        node: {
          extensions: ['.js', '.jsx', '.ts', '.tsx', '.d.ts', '.css'],
        },
      },
      'boundaries/elements': elements,
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      boundaries,
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/jsx-uses-react': 'off',
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': 'error',

      // Límites de módulo (Screaming Architecture)
      'boundaries/element-types': [
        'error',
        {
          default: 'disallow',
          rules: [
            { from: 'app', allow: ['app', 'features', 'shared', 'core'] },
            {
              from: 'features',
              allow: ['shared', 'core', ['features', { feature: '${from.feature}' }]],
            },
            { from: 'shared', allow: ['shared'] },
            { from: 'core', allow: ['core'] },
          ],
        },
      ],
      'boundaries/entry-point': [
        'error',
        {
          default: 'allow',
          rules: [{ target: ['features'], allow: 'index.ts' }],
        },
      ],
      'boundaries/no-unknown': 'error',
      'boundaries/no-unknown-files': 'error',
    },
  },
  {
    files: ['**/*.test.{ts,tsx}', 'src/test/**/*'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    // Ignorar archivos de configuración fuera de src
    files: [
      '*.config.{ts,js}',
      'eslint.config.js',
      'vitest.config.ts',
      'vite.config.ts',
      'playwright.config.ts',
    ],
    ignores: ['src/**'],
    rules: {
      'boundaries/no-unknown-files': 'off',
    },
  },
);
