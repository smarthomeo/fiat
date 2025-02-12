import { useState, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import FilterSidebar from "@/components/filters/FilterSidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, SlidersHorizontal, Bed, Bath, Users, Map, List } from "lucide-react";
import { mockStays } from "@/data/mockData";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useNavigate, useSearchParams } from "react-router-dom";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { addDays } from "date-fns";
import { LocationFilter } from '@/components/filters/LocationFilter';
import { SortSelect } from '@/components/filters/SortSelect';
import { GoogleMap, MarkerF, useLoadScript } from '@react-google-maps/api';
import { LoadingSpinner } from '@/components/ui/loading';

interface Stay {
  id: number;
  title: string;
  description: string;
  image: string;
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
}

const amenityOptions = [
  { id: 'wifi', label: 'WiFi', count: 150 },
  { id: 'kitchen', label: 'Kitchen', count: 120 },
  { id: 'parking', label: 'Parking', count: 100 },
  { id: 'pool', label: 'Pool', count: 45 },
  { id: 'ac', label: 'Air Conditioning', count: 130 },
  { id: 'workspace', label: 'Workspace', count: 80 },
];

const propertyTypes = [
  { id: 'house', label: 'House', count: 89 },
  { id: 'apartment', label: 'Apartment', count: 120 },
  { id: 'cabin', label: 'Cabin', count: 34 },
  { id: 'villa', label: 'Villa', count: 23 },
];

const Stays = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState("");
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 1000]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [stays, setStays] = useState<Stay[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date(),
    to: addDays(new Date(), 7),
  });
  const [sortBy, setSortBy] = useState("price_asc");
  const [showMap, setShowMap] = useState(false);

  useEffect(() => {
    const fetchStays = async () => {
      try {
        const url = `${import.meta.env.VITE_API_URL}/stays?${searchParams.toString()}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch stays');
        const data = await response.json();
        setStays(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStays();
  }, [searchParams]);

  const filteredStays = stays.filter(stay => {
    // Apply search filter
    if (searchQuery && !stay.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !stay.description.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !stay.details.location.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Apply property type filter
    if (selectedTypes.length > 0 && !selectedTypes.some(type => 
      stay.title.toLowerCase().includes(type))) {
      return false;
    }

    // Apply amenities filter
    if (selectedAmenities.length > 0 && !selectedAmenities.every(amenity => 
      stay.details.amenities.some(a => a.toLowerCase().includes(amenity)))) {
      return false;
    }

    // Apply price filter
    if (stay.price_per_night < priceRange[0] || stay.price_per_night > priceRange[1]) {
      return false;
    }

    return true;
  });

  const handleTypeChange = (typeId: string) => {
    setSelectedTypes(prev =>
      prev.includes(typeId)
        ? prev.filter(id => id !== typeId)
        : [...prev, typeId]
    );
  };

  const handleAmenityChange = (amenityId: string) => {
    setSelectedAmenities(prev =>
      prev.includes(amenityId)
        ? prev.filter(id => id !== amenityId)
        : [...prev, amenityId]
    );
  };

  const handleReset = () => {
    setPriceRange([0, 1000]);
    setSelectedTypes([]);
    setSelectedAmenities([]);
    setSearchQuery("");
  };

  const handleSort = (value: string) => {
    setSortBy(value);
    const sortedStays = [...stays].sort((a, b) => {
      switch (value) {
        case "price_asc":
          return a.price_per_night - b.price_per_night;
        case "price_desc":
          return b.price_per_night - a.price_per_night;
        case "rating_desc":
          return b.host.rating - a.host.rating;
        case "distance_asc":
          // Calculate distance if location is available
          return 0;
        default:
          return 0;
      }
    });
    setStays(sortedStays);
  };

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Stays</h1>
          <div className="flex items-center gap-4">
            <SortSelect value={sortBy} onValueChange={handleSort} />
            <Button
              variant="outline"
              onClick={() => setShowMap(!showMap)}
              className="flex items-center gap-2"
            >
              {showMap ? <List className="w-4 h-4" /> : <Map className="w-4 h-4" />}
              {showMap ? 'Show List' : 'Show Map'}
            </Button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search stays..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <DatePickerWithRange
            className="w-full md:w-auto"
            date={{
              from: dateRange.from,
              to: dateRange.to,
            }}
            onDateChange={(range: any) => setDateRange(range)}
          />
          <Button
            variant="outline"
            className="md:hidden"
            onClick={() => setShowMobileFilters(!showMobileFilters)}
          >
            <SlidersHorizontal className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-8">
          {/* Filters */}
          <div className={`${showMobileFilters ? 'block' : 'hidden'} md:block`}>
            <FilterSidebar
              title="Filter Stays"
              priceRange={priceRange}
              onPriceChange={setPriceRange}
              categories={propertyTypes}
              selectedCategories={selectedTypes}
              onCategoryChange={handleTypeChange}
              amenities={amenityOptions}
              selectedAmenities={selectedAmenities}
              onAmenityChange={handleAmenityChange}
              onReset={handleReset}
              type="stay"
            />
          </div>

          {/* Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading ? (
              <div>Loading...</div>
            ) : filteredStays.map((stay) => (
              <Card 
                key={stay.id}
                className="group cursor-pointer hover:shadow-lg transition-all duration-300"
                onClick={() => navigate(`/stays/${stay.id}`)}
              >
                <div className="aspect-[4/3] overflow-hidden rounded-t-lg">
                  <img
                    src={stay.image || '/placeholder-stay.jpg'}
                    alt={stay.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{stay.title}</CardTitle>
                    <span className="text-lg font-semibold text-primary">
                      ${stay.price_per_night}/night
                    </span>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {stay.description}
                  </CardDescription>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Bed className="w-4 h-4" />
                      <span>{stay.details?.bedrooms || 1} bed</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Bath className="w-4 h-4" />
                      <span>{stay.details?.bathrooms || 1} bath</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{stay.details?.maxGuests || 2} guests</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <img
                        src={stay.host?.image || '/default-avatar.png'}
                        alt={stay.host?.name || 'Host'}
                        className="w-8 h-8 rounded-full object-cover"
                      />
                      <div>
                        <p className="text-sm font-medium">{stay.host?.name || 'Host'}</p>
                        <div className="flex items-center">
                          <span className="text-xs text-yellow-500">★</span>
                          <span className="text-xs ml-1">{stay.host?.rating || 4.5}</span>
                          <span className="text-xs text-muted-foreground ml-1">
                            ({stay.host?.reviews || 0})
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/stays/${stay.id}`);
                      }}
                    >
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Stays;