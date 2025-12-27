import React, { useEffect, useState } from "react";
import { Card, CardContent } from "../../../../components/ui/card";
import { fetchRecommendedProducts, Recommendation } from "../../../../api/recommend";
import { API_BASE_URL } from "../../../../api/client";

import img01 from "../../../../assets/01.png";
import img03 from "../../../../assets/03.png";
import img04 from "../../../../assets/04.png";
import img05 from "../../../../assets/05.png";

export const RecommendedProductsSection = (): JSX.Element => {
  const [user, setUser] = useState<{ name: string } | null>(null);
  const [recommendedProducts, setRecommendedProducts] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const slideImages = [img01, img03, img04, img05];
  const [currentSlide, setCurrentSlide] = useState(0);

  const userId = 1;

  useEffect(() => {
    fetchRecommendedProducts(userId)
      .then((data) => {
        console.log("📦 받은 추천 데이터:", data); // 로깅 추가
        setUser({ name: data.user_nickname ?? "사용자" });
        setRecommendedProducts(Array.isArray(data.recommendations)
          ? data.recommendations
          : []);
        setError(null);
      })
      .catch((err) => {
        console.error("[fetchRecommendedProducts] 에러 발생:", err);
        setError("추천 상품을 불러오지 못했습니다.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [userId]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slideImages.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [slideImages.length]);

  if (loading)
    return <div className="text-center py-10">🔄 추천 상품을 불러오는 중...</div>;

  if (error)
    return (
      <div className="text-center text-red-500 py-10">
        {error}
      </div>
    );

  return (
    <section className="w-full max-w-[990px] mx-auto my-8">
      {/* 배너 이미지 슬라이드 */}
      <Card className="w-full h-[350px] mb-8 overflow-hidden relative">
        <CardContent className="p-0 h-full relative">
          {slideImages.map((img, index) => (
            <img
              key={index}
              src={img}
              alt={`Slide ${index + 1}`}
              className={`
                absolute inset-0 w-full h-full object-cover object-center
                transition-opacity duration-700 ease-in-out
                ${index === currentSlide ? "opacity-100 z-10" : "opacity-0 z-0"}
              `}
            />
          ))}
        </CardContent>
      </Card>

      {/* 추천 텍스트 */}
      <div className="text-xl font-semibold mb-4 text-[#333]">
        {user?.name ? `${user.name}님을 위한 추천 상품` : "추천 상품"}
      </div>

      {/* 추천 상품 그리드 */}
      <div className="grid grid-cols-4 gap-6">
        {recommendedProducts.map((product) => {
          const fullImageUrl = product.image_url
            ? product.image_url.startsWith("http")
              ? product.image_url
              : `${API_BASE_URL}${product.image_url.startsWith("/") ? "" : "/"}${product.image_url}`
            : null;

          return (
            <div key={product.product_id} className="flex flex-col">
              <Card className="w-full mb-2">
                <CardContent className="p-0">
                  <div className="relative w-full h-[221px] bg-gray-100">
                    {fullImageUrl ? (
                      <img
                        src={fullImageUrl}
                        alt={product.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-sm text-gray-500">
                        이미지 없음
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
              <div className="text-black font-semibold text-base leading-snug">
                {product.title}
                <br />
                💰 {product.price.toLocaleString()}원
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
