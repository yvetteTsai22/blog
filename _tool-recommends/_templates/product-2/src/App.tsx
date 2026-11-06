import { ToolRecommendLandingPage } from "./components/ToolRecommendLandingPage";
import { productConfig } from "./config";

export default function App() {
  return <ToolRecommendLandingPage {...productConfig} />;
}
