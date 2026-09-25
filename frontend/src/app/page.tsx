import DashboardLayout from "./(dashboard)/layout";
import HomePage from "./(dashboard)/page";

export default function RootPage() {
  return (
    <DashboardLayout>
      <HomePage />
    </DashboardLayout>
  );
}
