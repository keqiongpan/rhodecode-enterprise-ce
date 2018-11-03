/* webpack.config.js */
require('style-loader');
require('css-loader');
var path = require('path');

const projectName = 'rhodecode-components';
let destinationDirectory = path.join(process.cwd(), 'rhodecode', 'public', 'js')

if (process.env.RC_STATIC_DIR) {
    destinationDirectory = process.env.RC_STATIC_DIR;
}

// doing it this way because it seems that plugin via grunt does not pick up .babelrc
let babelRCOptions = {
    "presets": [
        ["env", {
            "targets": {
                "browsers": ["last 2 versions"]
            }
        }]
    ],
    "plugins": ["transform-object-rest-spread"]
}

module.exports = {
    // Tell Webpack which file kicks off our app.
    entry: {
        main: path.resolve(__dirname, 'rhodecode/public/js/src/components/index.js'),
    },
    output: {
        filename: 'rhodecode-components.js',
        path: path.resolve(destinationDirectory)
    },
    // Tell Webpack which directories to look in to resolve import statements.
    // Normally Webpack will look in node_modules by default but since we’re overriding
    resolve: {
        modules: [
            path.resolve(__dirname, 'node_modules'),
        ]
    },
    // These rules tell Webpack how to process different module types.
    // Remember, *everything* is a module in Webpack. That includes
    // CSS, and (thanks to our loader) HTML.
    module: {
        rules: [
            {
                test: /style-polymer.css/,
                use: 'raw-loader'
            },
            {
                // If you see a file that ends in .html, send it to these loaders.
                test: /\.html$/,
                // This is an example of chained loaders in Webpack.
                // Chained loaders run last to first. So it will run
                // polymer-webpack-loader, and hand the output to
                // babel-loader. This let's us transpile JS in our `<script>` elements.
                use: [
                    {loader: 'babel-loader',
                    options: babelRCOptions},
                    {loader: 'polymer-webpack-loader',
                        options: {
                            processStyleLinks: true,
                        }
                    }
                ],
            },
            {
                // If you see a file that ends in .js, just send it to the babel-loader.
                test: /\.js$/,
                use: {loader: 'babel-loader', options: babelRCOptions}
                // Optionally exclude node_modules from transpilation except for polymer-webpack-loader:
                // exclude: /node_modules\/(?!polymer-webpack-loader\/).*/
            },
            // this is required because of bug:
            // https://github.com/webpack-contrib/polymer-webpack-loader/issues/49
            {
                test: /intl-messageformat.min.js/,
                use: 'imports-loader?this=>window'
            }
        ]
    },
    plugins: []
};
