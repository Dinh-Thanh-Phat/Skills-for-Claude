# Expo / React Native: testID Cross-Platform Guide

Hướng dẫn chi tiết về cách dùng `testID` trong Expo để Maestro selector hoạt động nhất quán
trên cả iOS và Android.

## Cơ chế hoạt động

```
React Native testID prop
         │
         ├── iOS    → UIAccessibilityElement.accessibilityIdentifier
         │              Maestro: id: "my-value"
         │
         └── Android → View.setTag() / resource-id="com.example.app:id/my-value"
                        Maestro: id: "my-value"  (Maestro tự strip package prefix)
```

Maestro normalize cả hai platform về cùng một cú pháp `id:` — bạn không cần viết
selector khác nhau cho iOS vs Android.

## Rules of testID

### Rule 1: Dùng kebab-case, format `screen__element-type`

```tsx
// ✓ Rõ ràng, dễ tìm trong codebase
testID="auth__email-input"
testID="auth__login-button"
testID="checkout__confirm-order-button"
testID="cart__item-count-badge"
testID="profile__edit-avatar"
testID="orders__empty-state"
testID="orders__list-item-0"   // cho dynamic list items nếu cần
```

### Rule 2: Chỉ đặt trên native components, không trên custom wrappers

```tsx
// ❌ testID bị mất — MyButton không forward prop xuống TouchableOpacity
<MyButton testID="login-btn" label="Login" />

// ✓ Luôn forward testID trong custom component
const MyButton = ({ testID, label, onPress }: Props) => (
  <TouchableOpacity testID={testID} onPress={onPress}>
    <Text>{label}</Text>
  </TouchableOpacity>
);
```

### Rule 3: Expo components cần kiểm tra forward testID

Một số Expo components KHÔNG tự động forward testID:

```tsx
// expo-image — cần accessible={true} + testID
<Image
  source={{ uri: url }}
  testID="product__hero-image"
  accessible={true}           // bắt buộc trên iOS để testID hoạt động
/>

// Pressable (RN core) — hoạt động tốt
<Pressable testID="action__submit">
  <Text>Submit</Text>
</Pressable>

// ScrollView — testID cho container scroll
<ScrollView testID="feed__scroll-container">
  ...
</ScrollView>

// FlatList — testID trên mỗi item, không phải list
const renderItem = ({ item }) => (
  <View testID={`orders__item-${item.id}`}>
    <Text>{item.name}</Text>
  </View>
);
```

### Rule 4: Không dùng dynamic testID trong assertion (trừ khi cần)

```tsx
// ❌ Dynamic testID với index — fragile khi order thay đổi
testID={`item-${index}`}

// ✓ Dynamic testID với stable ID từ data
testID={`orders__item-${order.id}`}

// ✓ Stable testID cho known elements
testID="cart__checkout-button"   // luôn là 1 button duy nhất
```

## Cách verify testID đã đúng

### Trên Android (adb + uiautomator dump)

```bash
# Dump UI hierarchy ra XML
adb shell uiautomator dump /sdcard/ui.xml
adb pull /sdcard/ui.xml ./ui.xml

# Tìm resource-id của element
grep "resource-id" ui.xml | grep "example"
# → resource-id="com.example.app:id/auth__login-button"

# Maestro dùng: id: "auth__login-button"  (bỏ prefix)
```

### Trên iOS (Maestro Studio — cách nhanh nhất)

```bash
maestro studio
# → Mở browser tại localhost:9999
# → Tap vào element trong live preview
# → Inspector hiển thị accessibility ID = testID
```

### Trên iOS (Accessibility Inspector — Xcode)

```
Xcode → Open Developer Tool → Accessibility Inspector
→ Chọn Simulator
→ Hover lên element
→ Xem "Identifier" field = testID value
```

## Maestro selector đầy đủ với testID

```yaml
# Cơ bản
- tapOn:
    id: "auth__login-button"

# Kết hợp với điều kiện
- assertVisible:
    id: "orders__list-item"
    timeout: 10000

# Kết hợp với text để tránh nhầm
- tapOn:
    id: "auth__submit-button"
    text: "Login"               # double-check text — tránh nhầm khi có nhiều button

# Scroll đến element có testID
- scrollUntilVisible:
    element:
      id: "checkout__payment-section"
    direction: DOWN
    timeout: 8000
```

## Expo Router: testID cho navigation elements

```tsx
// Tab bar items
<Tabs.Screen
  name="home"
  options={{
    tabBarTestID: "nav__tab-home",    // ❌ tabBarTestID không phải standard prop
    tabBarButton: (props) => (
      <TouchableOpacity {...props} testID="nav__tab-home" />  // ✓ custom button
    ),
  }}
/>

// Stack header buttons
<Stack.Screen
  options={{
    headerRight: () => (
      <TouchableOpacity testID="header__settings-button" onPress={openSettings}>
        <Text>Settings</Text>
      </TouchableOpacity>
    ),
  }}
/>
```

## Android: Khi resource-id không hiển thị đúng

Một số trường hợp Android không tự map testID thành resource-id:

```tsx
// Thêm importantForAccessibility để đảm bảo testID được expose
<View
  testID="orders__empty-state"
  importantForAccessibility="yes"   // Android: đảm bảo element xuất hiện trong accessibility tree
>
  <Text>No orders yet</Text>
</View>

// Cho Text elements — cần accessible={true}
<Text
  testID="product__price-label"
  accessible={true}
>
  $99.99
</Text>
```

## iOS: Khi accessibilityIdentifier không hoạt động

```tsx
// accessibilityIdentifier = testID trên iOS
// Nếu Maestro không tìm thấy, thêm:
<TouchableOpacity
  testID="auth__login-button"
  accessibilityLabel="Login button"     // thêm label làm fallback
  accessibilityRole="button"            // giúp iOS accessibility tree nhận diện đúng
  onPress={handleLogin}
>
  <Text>Login</Text>
</TouchableOpacity>
```

## Checklist trước khi viết Maestro flow

```
[ ] Mọi interactive element có testID?
[ ] Custom components forward testID xuống native element?
[ ] testID naming theo convention screen__element-type?
[ ] Verify trên Android: uiautomator dump hoặc Maestro Studio?
[ ] Verify trên iOS: Accessibility Inspector hoặc Maestro Studio?
[ ] Dynamic list items dùng stable ID (item.id) thay vì index?
[ ] Text elements có accessible={true} nếu cần assert trên Android?
```
