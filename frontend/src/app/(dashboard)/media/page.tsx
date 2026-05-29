'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Image, Video, Wand2, Download, RefreshCw, Upload, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { mediaApi } from '@/lib/api';

type Tab = 'images' | 'videos';
type ImageProvider = 'flux' | 'dalle3' | 'ideogram';

export default function MediaStudioPage() {
  const [activeTab, setActiveTab] = useState<Tab>('images');
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState<ImageProvider>('flux');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [generating, setGenerating] = useState(false);
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: gallery } = useQuery({
    queryKey: ['media-gallery', activeTab],
    queryFn: () => mediaApi.getGallery(activeTab),
  });

  const generateMutation = useMutation({
    mutationFn: (data: { prompt: string; provider: ImageProvider; aspect_ratio: string }) =>
      mediaApi.generateImage(data),
    onSuccess: (data) => {
      setGeneratedUrl(data.data.url);
      toast.success('Image generated!');
      queryClient.invalidateQueries({ queryKey: ['media-gallery'] });
    },
    onError: () => toast.error('Generation failed'),
  });

  const handleGenerate = async () => {
    if (!prompt.trim()) return toast.error('Enter a prompt');
    setGenerating(true);
    setGeneratedUrl(null);
    try {
      await generateMutation.mutateAsync({ prompt, provider, aspect_ratio: aspectRatio });
    } finally {
      setGenerating(false);
    }
  };

  const SED_PROMPT_SUGGESTIONS = [
    'Solar panels on a modern South African home, golden hour lighting, professional photography',
    'Sungrow inverter installation, clean white wall, dramatic product shot',
    'Solar battery backup system, Astronergy panels, suburban house',
    'Happy South African family with solar power, bright sunny day, lifestyle shot',
    'Commercial solar farm aerial view, South African landscape, sunrise',
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Media Studio</h1>
        <p className="text-gray-400 mt-1">AI-powered image and video generation for SED content</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        {(['images', 'videos'] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'text-sed-orange border-b-2 border-sed-orange'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'images' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Generator */}
          <div className="bg-gray-800 rounded-xl p-6 space-y-4">
            <h2 className="text-white font-semibold flex items-center gap-2">
              <Wand2 className="w-4 h-4 text-sed-orange" />
              Image Generator
            </h2>

            <div>
              <label className="text-gray-400 text-sm block mb-2">Prompt</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                placeholder="Describe the image you want to generate..."
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm resize-none focus:outline-none focus:border-sed-orange"
              />
            </div>

            {/* Prompt suggestions */}
            <div>
              <p className="text-gray-500 text-xs mb-2">Quick prompts:</p>
              <div className="space-y-1">
                {SED_PROMPT_SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setPrompt(s)}
                    className="text-xs text-gray-400 hover:text-sed-orange text-left w-full truncate"
                  >
                    → {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-gray-400 text-sm block mb-2">Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value as ImageProvider)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="flux">Flux SDXL (Replicate)</option>
                  <option value="dalle3">DALL-E 3 (OpenAI)</option>
                  <option value="ideogram">Ideogram</option>
                </select>
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-2">Aspect Ratio</label>
                <select
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="1:1">1:1 (Square)</option>
                  <option value="16:9">16:9 (Landscape)</option>
                  <option value="9:16">9:16 (Portrait/Reels)</option>
                  <option value="4:5">4:5 (Instagram)</option>
                  <option value="1.91:1">1.91:1 (Facebook)</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="w-full bg-sed-orange hover:bg-orange-600 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4" />
                  Generate Image
                </>
              )}
            </button>
          </div>

          {/* Preview */}
          <div className="bg-gray-800 rounded-xl p-6">
            <h2 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Image className="w-4 h-4 text-sed-orange" />
              Preview
            </h2>

            {generatedUrl ? (
              <div className="space-y-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={generatedUrl}
                  alt="Generated"
                  className="w-full rounded-lg object-cover"
                />
                <div className="flex gap-2">
                  <a
                    href={generatedUrl}
                    download="sed-generated.png"
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 border border-gray-600 text-white py-2 rounded-lg text-sm flex items-center justify-center gap-2 hover:border-sed-orange"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </a>
                  <button
                    onClick={handleGenerate}
                    className="flex-1 border border-gray-600 text-white py-2 rounded-lg text-sm flex items-center justify-center gap-2 hover:border-sed-orange"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-700 rounded-lg">
                <div className="text-center">
                  <Image className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Generated image will appear here</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'videos' && (
        <div className="bg-gray-800 rounded-xl p-8 text-center">
          <Video className="w-16 h-16 mx-auto mb-4 text-sed-orange opacity-50" />
          <h3 className="text-white font-semibold text-lg mb-2">Video Generation</h3>
          <p className="text-gray-400 text-sm max-w-md mx-auto">
            Video generation via Runway ML Gen-3 is triggered automatically during content
            generation for video post types. Configure your Runway API key in Settings to enable.
          </p>
        </div>
      )}

      {/* Gallery */}
      {gallery && gallery.items?.length > 0 && (
        <div>
          <h2 className="text-white font-semibold mb-4">Recent Media</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {gallery.items.map((item: { id: string; url: string; created_at: string }) => (
              <div key={item.id} className="aspect-square rounded-lg overflow-hidden bg-gray-800 group relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={item.url} alt="" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <a href={item.url} target="_blank" rel="noreferrer">
                    <Download className="w-5 h-5 text-white" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
