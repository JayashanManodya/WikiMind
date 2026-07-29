import React, { useEffect, useRef } from 'react';

export default function GoogleAuthBtn({ clientId, onSuccess, onError }) {
  const btnRef = useRef(null);

  useEffect(() => {
    const loadGoogleSdk = () => {
      if (window.google?.accounts?.id) {
        initGoogleSignIn();
        return;
      }

      const existingScript = document.getElementById('google-jssdk');
      if (!existingScript) {
        const script = document.createElement('script');
        script.id = 'google-jssdk';
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => initGoogleSignIn();
        script.onerror = () => {
          if (onError) onError('Failed to load Google Identity SDK');
        };
        document.body.appendChild(script);
      } else {
        existingScript.addEventListener('load', initGoogleSignIn);
      }
    };

    const initGoogleSignIn = () => {
      if (!window.google?.accounts?.id) return;

      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => {
            if (response && response.credential) {
              if (onSuccess) onSuccess({ credential: response.credential });
            } else {
              if (onError) onError('No credential received');
            }
          },
        });

        if (btnRef.current) {
          btnRef.current.innerHTML = '';
          window.google.accounts.id.renderButton(btnRef.current, {
            theme: 'outline',
            size: 'large',
            text: 'signin_with',
            shape: 'pill',
            width: 280,
          });
        }
      } catch (err) {
        console.error("Google Auth initialization error:", err);
        if (onError) onError(err.message);
      }
    };

    loadGoogleSdk();
  }, [clientId, onSuccess, onError]);

  return <div ref={btnRef} style={{ minHeight: '40px', display: 'flex', justifyContent: 'center' }} />;
}
