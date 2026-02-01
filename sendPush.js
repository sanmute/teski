const webpush = require('web-push');

// IDE ILLIK A SAJÁT KULCSAID
webpush.setVapidDetails(
  'mailto:info@example.com',
  'BDauwcS32IU1DCT35Lpm0y4f6E1jVFOTjntdmgnofPwAH0nnzP8Zx8hPHz1f2D2Vbs4KL6uf4ECUGC3z3VGIfGQ',
  'DkOZsy6sKnnvlWyH5UW71WDGxXM1eN0BhMoZUmnCqf8'
);
// IDE ILLIK A FELIRATKOZÁSI ADAT A BÖNGÉSZŐBŐL
const subscription = {
  endpoint: '...',
  keys: {
    p256dh: '...',
    auth: '...'
  }
};

webpush.sendNotification(subscription, 'Hello Web Push!')
  .then(() => console.log("Push sent"))
  .catch(err => console.error("Error", err));
