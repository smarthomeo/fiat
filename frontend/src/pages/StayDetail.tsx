import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import MainLayout from "@/components/layout/MainLayout";
import { mockStays } from "@/data/mockData";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { Input } from "@/components/ui/input";
import {
  Bed,
  Bath,
  Users,
  Wifi,
  Car,
  Waves,
  Wind,
  Coffee,
  Laptop,
  MapPin,
  Star,
  Calendar,
} from "lucide-react";
import { addDays } from "date-fns";

const amenityIcons: Record<string, any> = {
  'WiFi': Wifi,
  'Parking': Car,
  'Pool': Waves,
  'Air Conditioning': Wind,
  'Kitchen': Coffee,
  'Workspace': Laptop,
};

const StayDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const stay = mockStays.find(s => s.id === id);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [dateRange, setDateRange] = useState({
    from: new Date(),
    to: addDays(new Date(), 7),
  });
  const [guests, setGuests] = useState({ adults: 1, children: 0 });

  if (!stay) {
    return (
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <h1>Stay not found</h1>
        </div>
      </MainLayout>
    );
  }

  // Calculate total nights and price
  const nights = dateRange.to ? Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60 * 24)) : 0;
  const basePrice = parseInt(stay.price.replace(/\D/g, ''));
  const totalPrice = basePrice * nights;

  const handleBooking = () => {
    console.log('Booking:', {
      stayId: id,
      dateRange,
      guests,
      totalPrice,
    });
    // Add booking logic here
  };

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">{stay.title}</h1>
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="w-4 h-4" />
            <span>{stay.details.location}</span>
          </div>
        </div>

        {/* Image Gallery */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="aspect-[4/3] rounded-lg overflow-hidden">
            <img
              src={stay.image}
              alt={stay.title}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="aspect-square rounded-lg overflow-hidden">
                <img
                  src={`/images/stays/details/${id}-${index + 1}.jpg`}
                  alt={`${stay.title} detail ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
          {/* Main Content */}
          <div className="space-y-8">
            {/* Host Info */}
            <div className="flex items-center justify-between pb-6 border-b">
              <div className="flex items-center gap-4">
                <img
                  src={stay.host.image}
                  alt={stay.host.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <h2 className="text-lg font-semibold">Hosted by {stay.host.name}</h2>
                  <div className="flex items-center text-muted-foreground">
                    <Star className="w-4 h-4 text-yellow-500 mr-1" />
                    <span>{stay.host.rating}</span>
                    <span className="mx-1">·</span>
                    <span>{stay.host.reviews} reviews</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Property Details */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Property Details</h2>
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <Bed className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{stay.details.bedrooms} bedrooms</p>
                    <p className="text-sm text-muted-foreground">{stay.details.beds} beds</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Bath className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{stay.details.bathrooms} bathrooms</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Up to {stay.details.maxGuests} guests</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Amenities */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Amenities</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {stay.details.amenities.map((amenity) => {
                  const IconComponent = amenityIcons[amenity] || Coffee;
                  return (
                    <div key={amenity} className="flex items-center gap-2">
                      <IconComponent className="w-5 h-5 text-muted-foreground" />
                      <span>{amenity}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Description */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">About this place</h2>
              <p className="text-muted-foreground leading-relaxed">
                {stay.description}
              </p>
            </div>
          </div>

          {/* Booking Card */}
          <div className="lg:sticky lg:top-24">
            <div className="rounded-lg border shadow-lg p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <span className="text-2xl font-bold">{stay.price}</span>
                  <span className="text-muted-foreground"> / night</span>
                </div>
                <div className="flex items-center">
                  <Star className="w-4 h-4 text-yellow-500 mr-1" />
                  <span className="font-medium">{stay.host.rating}</span>
                </div>
              </div>

              <div className="space-y-4">
                <DatePickerWithRange
                  date={{
                    from: dateRange.from,
                    to: dateRange.to,
                  }}
                  onDateChange={(range: any) => setDateRange(range)}
                />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Adults</label>
                    <Input
                      type="number"
                      min={1}
                      max={stay.details.maxGuests}
                      value={guests.adults}
                      onChange={(e) => setGuests({
                        ...guests,
                        adults: Number(e.target.value)
                      })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Children</label>
                    <Input
                      type="number"
                      min={0}
                      max={stay.details.maxGuests - guests.adults}
                      value={guests.children}
                      onChange={(e) => setGuests({
                        ...guests,
                        children: Number(e.target.value)
                      })}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between text-sm">
                    <span>{stay.price} x {nights} nights</span>
                    <span>${totalPrice}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Cleaning fee</span>
                    <span>$60</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Service fee</span>
                    <span>$40</span>
                  </div>
                  <div className="pt-4 border-t flex justify-between font-semibold">
                    <span>Total</span>
                    <span>${totalPrice + 100}</span>
                  </div>
                </div>

                <Button 
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white"
                  onClick={handleBooking}
                >
                  Reserve
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default StayDetail;