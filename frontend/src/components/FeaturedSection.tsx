import { useEffect, useState } from "react";
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { useNavigate } from 'react-router-dom';

interface FeaturedItem {
  id: number;
  title: string;
  description: string;
  image: string;
  price_per_person?: number;
  price_per_night?: number;
  host: {
    name: string;
    rating: number;
    reviews: number;
  };
}

interface Category {
  id: string;
  title: string;
  description: string;
  image: string;
  count: number;
}

const ItemCard = ({ 
  item, 
  onClick, 
  priceLabel, 
  showRating 
}: { 
  item: FeaturedItem | Category; 
  onClick: () => void; 
  priceLabel?: string; 
  showRating?: boolean; 
}) => (
  <div 
    className="group cursor-pointer transition-all duration-300"
    onClick={onClick}
  >
    <div className="relative overflow-hidden rounded-xl shadow-md hover:shadow-xl transition-shadow duration-300">
      <div className="aspect-[4/3] overflow-hidden">
        <img
          src={item.image}
          alt={item.title}
          className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
      <div className="p-5 bg-white">
        <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
          {item.title}
        </h3>
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
          {item.description}
        </p>
        {(priceLabel || showRating) && (
          <div className="flex justify-between items-center">
            {priceLabel && (
              <span className="font-medium text-primary">{priceLabel}</span>
            )}
            {showRating && 'host' in item && (
              <div className="flex items-center gap-1">
                <span className="text-yellow-500">★</span>
                <span className="font-medium">{item.host.rating}</span>
                <span className="text-sm text-gray-500">
                  ({item.host.reviews})
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  </div>
);

const Section = <T extends { id: number | string }>({ 
  title, 
  items, 
  viewAllLink, 
  renderItem 
}: { 
  title: string; 
  items: T[]; 
  viewAllLink?: string; 
  renderItem: (item: T) => React.ReactNode; 
}) => {
  const navigate = useNavigate();
  
  if (items.length === 0) return null;

  return (
    <section className="py-12">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-4xl font-bold tracking-tight text-gray-900 font-display">
            {title}
          </h2>
          {viewAllLink && (
            <Button 
              variant="outline" 
              onClick={() => navigate(viewAllLink)}
              className="text-base hover:bg-gray-100"
            >
              View All
            </Button>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {items.slice(0, 3).map((item) => renderItem(item))}
        </div>
      </div>
    </section>
  );
};

const cuisineCategories = [
  {
    id: 'african',
    title: 'African Cuisine',
    description: 'Explore rich flavors and traditional dishes from across Africa',
    image: '/images/african.jpg',
    count: 245
  },
  {
    id: 'italian',
    title: 'Italian Cuisine',
    description: 'Authentic pasta, pizza, and Mediterranean delights',
    image: '/images/italian.jpg',
    count: 189
  },
  {
    id: 'asian',
    title: 'Asian Cuisine',
    description: "From sushi to stir-fry, discover Asia's diverse flavors",
    image: '/images/asian.jpg',
    count: 203
  }
];

export const FeaturedSection = () => {
  const navigate = useNavigate();
  const [featuredFood, setFeaturedFood] = useState<FeaturedItem[]>([]);
  const [featuredStays, setFeaturedStays] = useState<FeaturedItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [foodRes, staysRes] = await Promise.all([
          fetch('http://localhost:5000/api/featured-food'),
          fetch('http://localhost:5000/api/featured-stays')
        ]);

        if (!foodRes.ok || !staysRes.ok) {
          throw new Error('Failed to fetch data');
        }

        const [foodData, staysData] = await Promise.all([
          foodRes.json(),
          staysRes.json()
        ]);

        setFeaturedFood(Array.isArray(foodData) ? foodData : []);
        setFeaturedStays(Array.isArray(staysData) ? staysData : []);
        setCategories(cuisineCategories);
      } catch (error) {
        console.error('Error fetching featured data:', error);
        setError('Failed to load featured content');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-16">
      <Section
        title="Popular Food Experiences"
        items={featuredFood}
        viewAllLink="/food"
        renderItem={(item) => (
          <ItemCard
            key={item.id}
            item={item}
            onClick={() => navigate(`/food/${item.id}`)}
            priceLabel={`$${item.price_per_person} per person`}
            showRating
          />
        )}
      />

      <Section
        title="Browse by Category"
        items={categories}
        renderItem={(category) => (
          <ItemCard
            key={category.id}
            item={category}
            onClick={() => navigate(`/food?category=${category.id}`)}
          />
        )}
      />

      <Section
        title="Featured Stays"
        items={featuredStays}
        viewAllLink="/stays"
        renderItem={(item) => (
          <ItemCard
            key={item.id}
            item={item}
            onClick={() => navigate(`/stays/${item.id}`)}
            priceLabel={`$${item.price_per_night} per night`}
            showRating
          />
        )}
      />
    </div>
  );
};

export default FeaturedSection;