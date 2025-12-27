// src/api/recommend.ts
import { apiFetch, API_BASE_URL } from "./client";

export type Recommendation = {
  category_id: number;
  product_id: number;
  title: string;
  price: number;
  image_url: string | null;
};

export type RecommendationResponse = {
  user_nickname: string | null;
  recommendations: Recommendation[];
};

export async function fetchRecommendedProducts(userId: number): Promise<RecommendationResponse> {
  const endpoint = `/recommendations/home?user_id=${userId}`;
  console.log("🔍 요청 URL:", `${API_BASE_URL}${endpoint}`); 
  return apiFetch<RecommendationResponse>(endpoint);
}