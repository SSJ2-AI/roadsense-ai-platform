// Capacitor API wrappers
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Geolocation } from '@capacitor/geolocation';

export async function takePicture() {
  const image = await Camera.getPhoto({
    quality: 90,
    allowEditing: false,
    resultType: CameraResultType.Uri,
    source: CameraSource.Camera
  });
  return image.webPath;
}

export async function getCurrentLocation() {
  const position = await Geolocation.getCurrentPosition();
  return {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude
  };
}
