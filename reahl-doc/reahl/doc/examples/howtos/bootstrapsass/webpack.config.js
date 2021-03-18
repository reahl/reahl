//https://webpack.js.org/loaders/sass-loader/

const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');


module.exports = {
  entry: { 'main': './webpack/index.js',
           'theme': './webpack/theme.scss'
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist')
  },
  module: {
     rules: [
      {
        test: /\.scss$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
    ],
  },
  plugins: [ new MiniCssExtractPlugin({
      filename: '[name].css'
    })],
};


