import { AffiliateLandingPage } from "./components/AffiliateLandingPage";
import { productConfig } from "./config";

export default function App() {
  return <AffiliateLandingPage {...productConfig} />;
}
