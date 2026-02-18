import postcss from 'postcss'
import tailwindcss from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'

export default postcss({
  plugins: [
    tailwindcss,
    tailwindcssAnimate,
  ],
})