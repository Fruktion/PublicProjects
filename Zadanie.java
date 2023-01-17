import java.util.ArrayList;
import java.util.Scanner;

class Samochod {
    private String company;
    private int price;
    private int year;

    public Samochod(String company, int price, int year) {
        this.company = company;
        this.price = price;
        this.year = year;
    }

    public String getCompany() {
        return company;
    }

    public int getPrice() {
        return price;
    }

    public int getYear() {
        return year;
    }

    @Override
    public String toString() {
        return "Samochod{" +
                "company='" + company + '\'' +
                ", price=" + price +
                ", year=" + year +
                '}';
    }
}

class Wyjatek extends Exception {
    private ArrayList<Samochod> cars;

    public Wyjatek(ArrayList<Samochod> cars) {
        this.cars = cars;
    }

    public ArrayList<Samochod> getCars() {
        return cars;
    }
}

public class Main {
    public static void main(String[] args) {
        ArrayList<Samochod> carList = new ArrayList<Samochod>();
        // Create a list of cars with randomly chosen parameters: company, price, year.
        Scanner input = new Scanner(System.in);
        System.out.print("Enter the number of cars you want to create: ");
        int n = input.nextInt();
        String[] companies = {"POLONEZ", "FIAT", "SYRENA"};
        for (int i = 0; i < n; i++) {
            String company = companies[(int)(Math.random()*companies.length)];
            int price = (int)(Math.random()*100000);
            int year = (int)(Math.random()*50)+1970;
            carList.add(new Samochod(company, price, year));
        }
        System.out.println("Cars created: ");
        for (Samochod car : carList) {
            System.out.println(car);
        }
        // User chooses the criterium of searching for cars: the oldest, not older than YEAR, the youngest, not younger than YEAR; and gives the YEAR as an input (if necessary).
        System.out.print("Enter R for return or W for exception: ");
        String option = input.next();
        System.out.print("Enter the criteria for searching cars (oldest, not older than, youngest, not younger than): ");
        String criteria = input.next();
        ArrayList<Samochod> foundCars = new ArrayList<Samochod>();
        if (criteria.equals("oldest")) {
            int oldestYear = Integer.MAX_VALUE;
            for (Samochod car : carList) {
                if (car.getYear() < oldestYear) {
                    oldestYear = car.getYear();
                }
            }
            for (Samochod car : carList) {
                if (car.getYear() == oldestYear)
                    foundCars.add(car);
            }
        } else if (criteria.equals("not older than")) {
            System.out.print("Enter the year: ");
            int year = input.nextInt();
            for (Samochod car : carList) {
                if (car.getYear() <= year) {
                    foundCars.add(car);
                }
            }
        } else if (criteria.equals("youngest")) {
            int youngestYear = Integer.MIN_VALUE;
            for (Samochod car : carList) {
                if (car.getYear() > youngestYear) {
                    youngestYear = car.getYear();
                }
            }
            for (Samochod car : carList) {
                if (car.getYear() == youngestYear) {
                    foundCars.add(car);
                }
            }
        } else if (criteria.equals("not younger than")) {
            System.out.print("Enter the year: ");
            int year = input.nextInt();
            for (Samochod car : carList) {
                if (car.getYear() >= year) {
                    foundCars.add(car);
                }
            }
        }
        // Showing all found cars (matching the chosen criteria) with their description.
        System.out.println("Found cars: ");
        for (Samochod car : foundCars) {
            System.out.println(car);
        }
        // Method of searching for cars has to be chosen from the user input:
        // R: method searches for cars and returns their list,
        // W: method searches for cars and throws an exception containing their list.
        if (option.equals("R")) {
            // return the list of found cars
        } else if (option.equals("W")) {
            throw new Wyjatek(foundCars);
        }
        input.close();
    }
}
