// frontend/tailwind.config.js
module.exports = {
    content: [
      "./src/**/*.{js,jsx,ts,tsx}",
    ],
    darkMode: 'class', // или 'media' для использования системных настроек
    theme: {
      extend: {
        typography: (theme) => ({
          DEFAULT: {
            css: {
              color: theme('colors.gray.900'),
              a: {
                color: theme('colors.indigo.600'),
                '&:hover': {
                  color: theme('colors.indigo.800'),
                },
              },
              'code::before': {
                content: '""',
              },
              'code::after': {
                content: '""',
              },
            },
          },
          dark: {
            css: {
              color: theme('colors.gray.100'),
              a: {
                color: theme('colors.indigo.400'),
                '&:hover': {
                  color: theme('colors.indigo.300'),
                },
              },
              h1: {
                color: theme('colors.gray.100'),
              },
              h2: {
                color: theme('colors.gray.100'),
              },
              h3: {
                color: theme('colors.gray.100'),
              },
              h4: {
                color: theme('colors.gray.100'),
              },
              h5: {
                color: theme('colors.gray.100'),
              },
              h6: {
                color: theme('colors.gray.100'),
              },
              strong: {
                color: theme('colors.gray.100'),
              },
              code: {
                color: theme('colors.gray.100'),
              },
              blockquote: {
                color: theme('colors.gray.100'),
                borderLeftColor: theme('colors.gray.700'),
              },
            },
          },
        }),
      },
    },
    variants: {
      extend: {
        typography: ['dark'],
      },
    },
    plugins: [
      require('@tailwindcss/typography'),
      require('@tailwindcss/forms'),
    ],
  };