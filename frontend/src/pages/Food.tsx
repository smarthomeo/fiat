import { useState, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import FilterSidebar from "@/components/filters/FilterSidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, SlidersHorizontal, Clock, Users, Map, List } from "lucide-react";
import { mockFoodExperiences, categories } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useNavigate, useSearchParams } from "react-router-dom";
import { LocationFilter } from '@/components/filters/LocationFilter';
import { GoogleMap, MarkerF, useLoadScript } from '@react-google-maps/api';
import { LoadingSpinner } from '@/components/ui/loading';
import { SortSelect } from '@/components/filters/SortSelect';
import { FoodCard } from "@/components/cards/FoodCard";
import { ErrorBoundary } from '@/components/ErrorBoundary';
interface FoodExperience {
  id: number;
  title: string;
  description: string;
  images: { url: string }[];
  price_per_person: number;
  cuisine_type: string;
  host: {
    name: string;
    rating: number;
    reviews: number;
  };
  location_name: string;
  latitude: number;
  longitude: number;
}

interface FoodListing {
  id: number;
  title: string;
  description: string;
  price_per_person: number;
  images: string[];
  latitude: number;
  longitude: number;
  // ... other fields
}

const cuisineTypes = categories.map(cat => ({
  id: cat.id,
  label: cat.title,
  count: cat.count,
}));

const priceRanges = [
  { id: 'under-50', label: 'Under $50', count: 120 },
  { id: '50-100', label: '$50 - $100', count: 85 },
  { id: '100-150', label: '$100 - $150', count: 45 },
  { id: 'over-150', label: 'Over $150', count: 25 },
];

const Food = () => {
  const [searchParams] = useSearchParams();
  const [experiences, setExperiences] = useState<FoodExperience[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("rating_desc");
  const navigate = useNavigate();

  useEffect(() => {
    const params: Record<string, string> = {
      sort: sortBy
    };

    // Add zipcode from URL if present
    const zipcode = searchParams.get('zipcode');
    if (zipcode) {
      params.zipcode = zipcode;
    }

    fetchExperiences(params);
  }, [searchParams, sortBy]);

  const fetchExperiences = async (params = {}) => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams(params);
      const url = `http://localhost:5000/api/food-experiences?${queryParams}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch experiences');
      }
      
      const data = await response.json();
      setExperiences(data);
    } catch (error) {
      console.error('Error fetching experiences:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationFilter = (params: { latitude: number; longitude: number; radius: number }) => {
    fetchExperiences({
      sort: sortBy,
      ...params
    });
  };

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Filters Section */}
          <div className="w-full md:w-64 space-y-4">
            <LocationFilter onFilter={handleLocationFilter} />
            <div className="mt-4">
              <SortSelect
                value={sortBy}
                onValueChange={(value) => setSortBy(value)}
              />
            </div>
          </div>

          {/* Listings Section */}
          <div className="flex-1">
            {loading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : experiences.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {experiences.map((experience) => (
                  <ErrorBoundary key={experience.id}>
                    <FoodCard
                      experience={experience}
                      onClick={() => navigate(`/food/${experience.id}`)}
                    />
                  </ErrorBoundary>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-lg text-gray-600">No food experiences found.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Food;
