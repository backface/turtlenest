const { addDynamicIconSelectors } = require('@iconify/tailwind');

const colors = require('tailwindcss/colors')

const path = require('path');
const projectRoot = path.resolve(__dirname, './');

const { spawnSync } = require('child_process');

// Function to execute the Django management command and capture its output
const getTemplateFiles = () => {
  const command = 'poetry'; // Requires virtualenv to be activated.
  const args = ['run', 'python', 'manage.py', 'list_templates']; // Requires cwd to be set.
  const options = { cwd: projectRoot };
  const result = spawnSync(command, args, options);

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    console.log(result.stdout.toString(), result.stderr.toString());
    throw new Error(`Django management command exited with code ${result.status}`);
  }

  const templateFiles = result.stdout.toString()
    .split('\n')
    .map((file) => file.trim())
    .filter(function(e){return e});  // Remove empty strings, including last empty line.
  return templateFiles;
};



/** @type {import('tailwindcss').Config} */
module.exports = {
  // content: [
  //     "templates/**/*.{html,js}",
  // ],
  content: [].concat(getTemplateFiles()),
  // prefix: "tw-",
  // important: true,
  // corePlugins: {
  //     preflight: false,
  // },  
  darkMode: ['selector', '[data-mode="light"]'],
  daisyui: {
    themes: ["light"],
  },
  theme: {
    
    fontFamily: {
      //sans: ['Graphik', 'sans-serif'],
      //serif: ['Merriweather', 'serif'],
    },
    extend: {
      aspectRatio: {
        '4/3': '4 / 3',
        '3/2': '3 / 2',      
      },
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      colors: {
        primary: '#59b35f',
        secondary: '#008b78',
        tertiary: '#188a4c',
        blue: "#4a6cd4",
        dark: "#2c2c2c",
        light: "#f6f6f6"
      },
      gridTemplateRows: {
        'layout': 'auto 1fr auto',
        'creation': '1fr 100px 1fr',
      },
      
   }
  },
  plugins: [
    // require("daisyui"),
    addDynamicIconSelectors(),
    require('daisyui'),
  ]
}

