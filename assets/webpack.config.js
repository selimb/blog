const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const { WebpackManifestPlugin } = require("webpack-manifest-plugin");

const IS_PRODUCTION = process.env.NODE_ENV === "production";
const HERE = path.resolve(__dirname);
const REPO_DIR = path.resolve(HERE, "..");

// https://blog.frankdejonge.nl/setting-up-docs-with-tailwind-css-and-github-pages/
// fullstackphoenix with tailwind
module.exports = {
  mode: IS_PRODUCTION ? "production" : "development",
  entry: {
    main: path.resolve(HERE, "src", "index.js"),
  },
  output: {
    path: path.resolve(HERE, "dist/"),
    filename: IS_PRODUCTION ? "[name].[contenthash].js" : "[name].js",
    chunkFilename: IS_PRODUCTION ? "[id].[contenthash].js" : "[id].js",
    clean: true,
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: IS_PRODUCTION ? "[name].[contenthash].css" : "[name].css",
    }),
    new WebpackManifestPlugin({ publicPath: "./dist/" }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        exclude: /node_modules/,
        use: [MiniCssExtractPlugin.loader, "css-loader", "postcss-loader"],
      },
    ],
  },
};
