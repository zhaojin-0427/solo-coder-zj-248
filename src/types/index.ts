export interface KitListing {
  id: number
  user_id: number
  title: string
  type: 'sell' | 'buy'
  price: number
  description: string
  scale: string
  manufacturer: string
  condition: string
  subject: string
  missing_parts: string
  images: string[]
  status: string
  created_at: string
}

export interface KitMatch {
  id: number
  sell_listing_id: number
  buy_listing_id: number
  match_score: number
  created_at: string
}

export interface TutorialStep {
  id: number
  tutorial_id: number
  order_num: number
  title: string
  description: string
  technique: string
  image: string
}

export interface PaintRecord {
  id: number
  tutorial_id: number
  name: string
  brand: string
  color_code: string
  usage: string
}

export interface WeatheringDetail {
  id: number
  tutorial_id: number
  type: string
  products: string[]
  technique: string
  description: string
}

export interface Tutorial {
  id: number
  user_id: number
  title: string
  subject: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  cover_image: string
  views: number
  completions: number
  favorites: number
  created_at: string
  steps?: TutorialStep[]
  paints?: PaintRecord[]
  weathering_details?: WeatheringDetail[]
}

export interface Artwork {
  id: number
  user_id: number
  title: string
  subject: string
  scale: string
  kit_name: string
  images: string[]
  paints: string[]
  techniques: string[]
  weathering: string[]
  likes: number
  favorites: number
  created_at: string
}

export interface Tool {
  id: number
  name: string
  category: string
  brand: string
  rating: number
  review_count: number
  description: string
  image: string
  recommended_by: string[]
}

export interface Favorite {
  id: number
  user_id: number
  target_type: string
  target_id: number
  created_at: string
}

export interface SubjectStat {
  scale: string
  subject: string
  count: number
}

export interface TurnoverStat {
  month: string
  avg_days: number
}

export interface CompletionStat {
  tutorial_id: number
  title: string
  views: number
  completions: number
  completion_rate: number
}

export interface FavoriteStat {
  technique: string
  favorite_count: number
}
