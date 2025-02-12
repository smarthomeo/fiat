import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import MainLayout from "@/components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Calendar, Clock, Users, MapPin, ChefHat, Globe } from "lucide-react";
import { ImageGallery } from "@/components/ImageGallery";

interface FoodExperience {
  id: number;
  title: string;
  description: string;
  images: { url: string; order: number }[];
  price_per_person: number;
  cuisine_type: string;
  menu_description: string;
  host: {
    name: string;
    image: string;
    rating: number;
    reviews: number;
  };
  details: {
    duration: string;
    groupSize: string;
    includes: string[];
    language: string;
    location: string;
  };
}

const FoodDetails = () => {
  const { id } = useParams();
  const [experience, setExperience] = useState<FoodExperience | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExperience = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/food-experiences/${id}`);
        if (!response.ok) throw new Error('Failed to fetch experience');
        const data = await response.json();
        setExperience(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchExperience();
  }, [id]);

  if (loading) return <div>Loading...</div>;
  if (!experience) return <div>Experience not found</div>;

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-bold mb-4">{experience.title}</h1>
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>{experience.details.location}</span>
              </div>
            </div>

            <ImageGallery images={experience.images} />

            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-4">About this experience</h2>
                <p className="text-muted-foreground whitespace-pre-line">
                  {experience.description}
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-semibold mb-4">Menu</h2>
                <p className="text-muted-foreground whitespace-pre-line">
                  {experience.menu_description}
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-semibold mb-4">What's included</h2>
                <ul className="list-disc list-inside text-muted-foreground">
                  {experience.details.includes.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <span className="text-2xl font-bold">
                  ${experience.price_per_person}
                </span>
                <span className="text-muted-foreground">per person</span>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span>{experience.details.duration}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>{experience.details.groupSize}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ChefHat className="w-4 h-4" />
                  <span>{experience.cuisine_type}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  <span>{experience.details.language}</span>
                </div>
              </div>

              <Button className="w-full">
                Contact Host
              </Button>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-4">
                <img
                  src={experience.host.image}
                  alt={experience.host.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <h3 className="font-semibold">Hosted by {experience.host.name}</h3>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <span className="text-yellow-500">★</span>
                    <span className="ml-1">{experience.host.rating}</span>
                    <span className="ml-1">
                      ({experience.host.reviews} reviews)
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default FoodDetails; 