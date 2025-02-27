import { createTheme } from '@rneui/themed';

export const theme = createTheme({
  lightColors: {
    primary: '#4285F4',
    secondary: '#9C27B0',
    background: '#FFFFFF',
    error: '#FF5252',
    success: '#4CAF50',
    warning: '#FFC107',
    grey0: '#F5F5F5',
    grey1: '#E0E0E0',
  },
  mode: 'light',
  components: {
    Button: {
      raised: true,
      radius: 8,
    },
    Card: {
      containerStyle: {
        borderRadius: 8,
        elevation: 3,
      },
    },
  },
}); 