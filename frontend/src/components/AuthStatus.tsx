import React, { useState } from 'react';
import {
  Box,
  Avatar,
  Button,
  Menu,
  MenuItem,
  Typography,
  Chip,
  Divider,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Person,
  Logout,
  ExpandMore,
} from '@mui/icons-material';
import { SpotifyAuthData } from '../services/auth';
import { SpotifyIcon } from './ServiceIcons';

interface AuthStatusProps {
  authData: SpotifyAuthData | null;
  onSignOut: () => void;
}

const AuthStatus: React.FC<AuthStatusProps> = ({ authData, onSignOut }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSignOut = () => {
    handleClose();
    onSignOut();
  };

  // If not authenticated, show a simple indicator
  if (!authData) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          icon={<Person />}
          label="Not signed in"
          variant="outlined"
          size="small"
          sx={{
            color: 'text.secondary',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
            },
          }}
        />
      </Box>
    );
  }

  // If authenticated, show user info with dropdown
  const user = authData.user;
  const userImage = user.images && user.images.length > 0 ? user.images[0].url : undefined;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Button
        onClick={handleClick}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          textTransform: 'none',
          color: 'text.primary',
          borderRadius: '20px',
          px: 2,
          py: 1,
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(124, 58, 237, 0.15)',
          backdropFilter: 'blur(8px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderColor: 'rgba(124, 58, 237, 0.25)',
            boxShadow: '0 6px 16px rgba(0,0,0,0.2)',
          },
        }}
        endIcon={<ExpandMore />}
      >
        <Avatar
          src={userImage}
          sx={{
            width: 24,
            height: 24,
            fontSize: '12px',
          }}
        >
          {user.display_name?.charAt(0).toUpperCase()}
        </Avatar>
        <Typography
          variant="body2"
          sx={{
            fontWeight: 500,
            display: { xs: 'none', sm: 'block' }, // Hide username on mobile
            maxWidth: '120px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {user.display_name}
        </Typography>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: 200,
            backgroundColor: 'rgba(16, 18, 30, 0.95)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(124, 58, 237, 0.15)',
            borderRadius: 2,
          },
        }}
      >
        {/* User Info Header */}
        <Box sx={{ px: 2, py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar
              src={userImage}
              sx={{ width: 32, height: 32 }}
            >
              {user.display_name?.charAt(0).toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {user.display_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user.email}
              </Typography>
            </Box>
          </Box>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        {/* Service Info */}
        <MenuItem disabled>
          <ListItemIcon>
            <Box sx={{ fontSize: '20px' }}>
              <SpotifyIcon />
            </Box>
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">
              Connected to Spotify
            </Typography>
          </ListItemText>
        </MenuItem>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

        {/* Sign Out */}
        <MenuItem onClick={handleSignOut}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">
              Sign out
            </Typography>
          </ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default AuthStatus;
