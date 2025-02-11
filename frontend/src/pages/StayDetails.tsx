import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import MainLayout from "@/components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Bed, Bath, Users, MapPin, Home, Wifi } from "lucide-react";
import { ImageGallery } from "@/components/ImageGallery";
import { DatePicker } from "@/components/ui/date-picker";
import { format } from "date-fns";

interface Stay {
  id: number;
  title: string;
  description: string;
  images: { url: string; order: number }[];
  price_per_night: number;
  host: {
    name: string;
    image: string;
    rating: number;
    reviews: number;
  };
  details: {
    bedrooms: number;
    beds: number;
    bathrooms: number;
    maxGuests: number;
    amenities: string[];
    location: string;
  };
  availability: {
    date: string;
    price: number;
    is_available: boolean;
  }[];
}

const StayDetails = () => {
  const { id } = useParams();
  const [stay, setStay] = useState<Stay | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());

  useEffect(() => {
    const fetchStay = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/stays/${id}`);
        if (!response.ok) throw new Error('Failed to fetch stay');
        const data = await response.json();
        setStay(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStay();
  }, [id]);

  if (loading) return <div>Loading...</div>;
  if (!stay) return <div>Stay not found</div>;

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            <div>
              <h1 className="text-3xl font-bold mb-4">{stay.title}</h1>
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>{stay.details.location}</span>
              </div>
            </div>

            <ImageGallery images={stay.images} />

            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-4">About this place</h2>
                <p className="text-muted-foreground whitespace-pre-line">
                  {stay.description}
                </p>
              </div>

              <div>
                <h2 className="text-2xl font-semibold mb-4">What this place offers</h2>
                <div className="grid grid-cols-2 gap-4">
                  {stay.details.amenities.map((amenity, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Wifi className="w-4 h-4" />
                      <span>{amenity}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <span className="text-2xl font-bold">
                  ${stay.price_per_night}
                </span>
                <span className="text-muted-foreground">per night</span>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex items-center gap-2">
                  <Bed className="w-4 h-4" />
                  <span>{stay.details.beds} beds</span>
                </div>
                <div className="flex items-center gap-2">
                  <Bath className="w-4 h-4" />
                  <span>{stay.details.bathrooms} bathrooms</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>Up to {stay.details.maxGuests} guests</span>
                </div>
                <div className="flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  <span>{stay.details.bedrooms} bedrooms</span>
                </div>
              </div>

              <div className="space-y-4">
                <DatePicker
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  availableDates={stay.availability
                    .filter(a => a.is_available)
                    .map(a => new Date(a.date))}
                />
                
                {selectedDate && (
                  <div className="space-y-2">
                    {stay.availability
                      .filter(a => a.date === format(selectedDate, 'yyyy-MM-dd'))
                      .map((slot, index) => (
                        <div key={index} className="flex justify-between items-center">
                          <span>Price for selected date:</span>
                          <span className="font-semibold">${slot.price}</span>
                        </div>
                      ))}
                  </div>
                )}

                <Button className="w-full">Book Now</Button>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-4">
                <img
                  src={stay.host.image}
                  alt={stay.host.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <h3 className="font-semibold">Hosted by {stay.host.name}</h3>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <span className="text-yellow-500">★</span>
                    <span className="ml-1">{stay.host.rating}</span>
                    <span className="ml-1">
                      ({stay.host.reviews} reviews)
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

export default StayDetails; 