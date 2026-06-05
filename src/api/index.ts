import axios from 'axios'
import type {
  KitListing,
  KitMatch,
  Tutorial,
  Artwork,
  Tool,
  SubjectStat,
  TurnoverStat,
  CompletionStat,
  FavoriteStat,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

export async function getListings(params?: Record<string, string>): Promise<KitListing[]> {
  const { data } = await api.get('/listings', { params })
  return data
}

export async function createListing(payload: Partial<KitListing>): Promise<KitListing> {
  const { data } = await api.post('/listings', payload)
  return data
}

export async function getListingDetail(id: number): Promise<KitListing> {
  const { data } = await api.get(`/listings/${id}`)
  return data
}

export async function getListingMatches(id: number): Promise<KitMatch[]> {
  const { data } = await api.get(`/listings/${id}/matches`)
  return data
}

export async function updateListingStatus(id: number, status: string): Promise<KitListing> {
  const { data } = await api.put(`/listings/${id}/status`, { status })
  return data
}

export async function getTutorials(params?: Record<string, string>): Promise<Tutorial[]> {
  const { data } = await api.get('/tutorials', { params })
  return data
}

export async function createTutorial(payload: Partial<Tutorial>): Promise<Tutorial> {
  const { data } = await api.post('/tutorials', payload)
  return data
}

export async function getTutorialDetail(id: number): Promise<Tutorial> {
  const { data } = await api.get(`/tutorials/${id}`)
  return data
}

export async function favoriteTutorial(id: number): Promise<{ favorited: boolean; favorites: number }> {
  const { data } = await api.post(`/tutorials/${id}/favorite`, null, { params: { user_id: 1 } })
  return data
}

export async function completeTutorial(id: number): Promise<void> {
  await api.post(`/tutorials/${id}/complete`)
}

export async function getArtworks(params?: Record<string, string>): Promise<Artwork[]> {
  const { data } = await api.get('/artworks', { params })
  return data
}

export async function createArtwork(payload: Partial<Artwork>): Promise<Artwork> {
  const { data } = await api.post('/artworks', payload)
  return data
}

export async function getArtworkDetail(id: number): Promise<Artwork> {
  const { data } = await api.get(`/artworks/${id}`)
  return data
}

export async function likeArtwork(id: number): Promise<void> {
  await api.post(`/artworks/${id}/like`)
}

export async function favoriteArtwork(id: number): Promise<{ favorited: boolean; favorites: number }> {
  const { data } = await api.post(`/artworks/${id}/favorite`, null, { params: { user_id: 1 } })
  return data
}

export async function getTools(params?: Record<string, string>): Promise<Tool[]> {
  const { data } = await api.get('/tools', { params })
  return data
}

export async function getToolDetail(id: number): Promise<Tool> {
  const { data } = await api.get(`/tools/${id}`)
  return data
}

export async function getPopularSubjects(): Promise<SubjectStat[]> {
  const { data } = await api.get('/statistics/popular-subjects')
  return data
}

export async function getTurnoverSpeed(): Promise<TurnoverStat[]> {
  const { data } = await api.get('/statistics/turnover-speed')
  return data
}

export async function getTutorialCompletion(): Promise<CompletionStat[]> {
  const { data } = await api.get('/statistics/tutorial-completion')
  return data
}

export async function getTechniqueFavorites(): Promise<FavoriteStat[]> {
  const { data } = await api.get('/statistics/technique-favorites')
  return data
}

export default api
