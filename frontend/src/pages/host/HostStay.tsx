import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";
import ImageUpload from "@/components/ImageUpload";
import { useAuth } from "@/contexts/AuthContext";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { AmenitiesSelect } from "@/components/AmenitiesSelect";
import { LocationInput } from '@/components/form/LocationInput';

const formSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().min(1, "Description is required"),
  location_name: z.string().min(1, "Location is required"),
  price_per_night: z.number().min(0, "Price must be positive"),
  max_guests: z.number().min(1, "Must have at least 1 guest"),
  bedrooms: z.number().min(1, "Must have at least 1 bedroom"),
  images: z.array(z.string()),
  status: z.enum(["draft", "published"]),
  amenities: z.array(z.number()),
  availability: z.array(z.object({
    date: z.string(),
    is_available: z.boolean(),
    price_override: z.number().optional()
  })),
  address: z.string().min(1, "Address is required"),
  zipcode: z.string().min(1, "Zipcode is required"),
  city: z.string().min(1, "City is required"),
  state: z.string().min(1, "State is required"),
  latitude: z.number().min(0, "Latitude must be positive"),
  longitude: z.number().min(0, "Longitude must be positive")
});

type FormData = z.infer<typeof formSchema>;

interface Amenity {
  id: string;
  name: string;
}

const HostStay = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { checkAuth } = useAuth();
  const [loading, setLoading] = useState(false);
  const [images, setImages] = useState<string[]>([]);
  const [selectedDates, setSelectedDates] = useState<Date[]>([]);
  const [selectedAmenities, setSelectedAmenities] = useState<Amenity[]>([]);
  const [location, setLocation] = useState({
    address: '',
    zipcode: '',
    city: '',
    state: '',
    latitude: 0,
    longitude: 0
  });

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: "",
      description: "",
      location_name: "",
      price_per_night: 0,
      max_guests: 1,
      bedrooms: 1,
      images: [],
      status: "draft",
      amenities: [],
      availability: [],
      address: '',
      zipcode: '',
      city: '',
      state: '',
      latitude: 0,
      longitude: 0
    }
  });

  useEffect(() => {
    if (id) {
      const fetchStay = async () => {
        try {
          const token = localStorage.getItem('token');
          const response = await fetch(`${import.meta.env.VITE_API_URL}/host/stays/${id}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          if (!response.ok) throw new Error('Failed to fetch stay');

          const data = await response.json();
          
          form.reset({
            title: data.title,
            description: data.description,
            location_name: data.location_name,
            price_per_night: Number(data.price_per_night),
            max_guests: Number(data.max_guests),
            bedrooms: Number(data.bedrooms),
            images: data.images.map((img: { url: string }) => img.url),
            status: data.status,
            amenities: data.amenities,
            availability: data.availability,
            address: data.address,
            zipcode: data.zipcode,
            city: data.city,
            state: data.state,
            latitude: Number(data.latitude),
            longitude: Number(data.longitude)
          });
        } catch (error) {
          console.error('Error:', error);
          toast({
            title: "Error",
            description: "Failed to fetch stay details",
            variant: "destructive",
          });
          navigate('/host/dashboard');
        }
      };

      fetchStay();
    }
  }, [id, form, navigate, toast]);

  useEffect(() => {
    const fetchAmenities = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/amenities?type=stay`);
        if (!response.ok) throw new Error('Failed to fetch amenities');
        const data = await response.json();
        setSelectedAmenities([]);
      } catch (error) {
        console.error('Error:', error);
        setSelectedAmenities([]);
      }
    };

    fetchAmenities();
  }, []);

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      // Add basic fields
      formData.append('title', data.title);
      formData.append('description', data.description);
      formData.append('location_name', data.location_name);
      formData.append('price_per_night', data.price_per_night.toString());
      formData.append('max_guests', data.max_guests.toString());
      formData.append('bedrooms', data.bedrooms.toString());
      formData.append('status', data.status);

      // Add images
      if (data.images && data.images.length > 0) {
        formData.append('images', JSON.stringify(data.images));
      }

      // Add amenities
      if (selectedAmenities && selectedAmenities.length > 0) {
        formData.append('amenities', JSON.stringify(selectedAmenities.map(a => a.id)));
      }

      // Add availability
      if (data.availability && data.availability.length > 0) {
        formData.append('availability', JSON.stringify(data.availability));
      }

      // Add location data
      formData.append('address', data.address);
      formData.append('zipcode', data.zipcode);
      formData.append('city', data.city);
      formData.append('state', data.state);
      formData.append('latitude', data.latitude.toString());
      formData.append('longitude', data.longitude.toString());

      const url = id 
        ? `${import.meta.env.VITE_API_URL}/host/stays/${id}`
        : `${import.meta.env.VITE_API_URL}/host/stays`;

      const response = await fetch(url, {
        method: id ? 'PUT' : 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to save stay');
      }

      toast({
        title: "Success",
        description: `Stay ${id ? 'updated' : 'created'} successfully`,
      });

      // Wait a bit before redirecting to ensure the server has processed the update
      setTimeout(() => {
        navigate('/host/dashboard');
      }, 1000);

    } catch (error) {
      console.error('Error saving stay:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save stay",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">
        {id ? 'Edit Stay' : 'Create Stay'}
      </h1>
      
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="Cozy Beach House" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Describe your property..."
                      className="h-32"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="location_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Location</FormLabel>
                  <FormControl>
                    <Input placeholder="123 Main St, City" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="price_per_night"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Price per Night</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        placeholder="99.99"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                        value={field.value}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_guests"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Guests</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        min="1"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                        value={field.value}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="bedrooms"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bedrooms</FormLabel>
                    <FormControl>
                      <Input 
                        type="number"
                        min="1"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                        value={field.value}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-4">
              <Label>Amenities</Label>
              <AmenitiesSelect
                selectedAmenities={selectedAmenities}
                onAmenitiesChange={(amenities) => {
                  setSelectedAmenities(amenities);
                  form.setValue('amenities', amenities.map(a => Number(a.id)));
                }}
              />
              <p className="text-sm text-muted-foreground">
                Select existing amenities or add your own
              </p>
            </div>

            <FormField
              control={form.control}
              name="images"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Images</FormLabel>
                  <FormControl>
                    <ImageUpload
                      value={field.value}
                      onChange={field.onChange}
                      onRemove={(url) => {
                        field.onChange(field.value.filter((val) => val !== url));
                      }}
                      title={form.getValues("title") || "stay"}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-4">
              <h3 className="text-lg font-medium">Availability</h3>
              <div className="flex space-x-4">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      Select Dates
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="multiple"
                      selected={selectedDates}
                      onSelect={setSelectedDates}
                      className="rounded-md border"
                    />
                  </PopoverContent>
                </Popover>
              </div>
              
              <div className="space-y-2">
                {selectedDates.map((date) => (
                  <div key={date.toISOString()} className="flex items-center space-x-4">
                    <span>{format(date, 'PPP')}</span>
                    <Input
                      type="number"
                      placeholder="Price override"
                      className="w-32"
                      onChange={(e) => {
                        const availability = form.getValues('availability') || [];
                        const newAvailability = [
                          ...availability,
                          {
                            date: format(date, 'yyyy-MM-dd'),
                            is_available: true,
                            price_override: Number(e.target.value)
                          }
                        ];
                        form.setValue('availability', newAvailability);
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Location</Label>
                <LocationInput
                  value={location}
                  onChange={setLocation}
                  error={form.getValues('address')}
                />
                <p className="text-sm text-muted-foreground">
                  Enter the address where you'll host your stay
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => form.setValue('status', 'draft')}
            >
              Save as Draft
            </Button>
            <Button
              type="submit"
              disabled={loading}
              onClick={() => form.setValue('status', 'published')}
            >
              {loading ? "Saving..." : id ? "Update Stay" : "Publish Stay"}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
};

export default HostStay;