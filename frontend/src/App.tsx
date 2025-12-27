import { NavigationBarSection } from "./screens/HomePage/sections/NavigationBarSection/index";
import { RecommendedProductsSection } from "./screens/HomePage/sections/RecommendedProductsSection/index";
import { FooterSection } from './screens/HomePage/sections/FooterSection/index';


function App() {
    return (
        <div className="min-h-screen bg-white">
            <NavigationBarSection />
            <RecommendedProductsSection />
            <FooterSection />
        </div>
    );
}

export default App;
