import { renderToString } from "react-dom/server";
import App from "./App.tsx";
import { seo } from "./config";

export function render() {
  return { html: renderToString(<App />), seo };
}
