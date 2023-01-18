import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

public class Main {
    private JFrame frame;
    private JTextField inputField;
    private JList<Double> numberList;
    private ArrayList<Double> numbers;
    private JButton addButton, deleteButton, editButton;
    private ChartPanel chartPanel;

    public Main() {
        // Initialize frame
        frame = new JFrame("Number Chart");
        frame.setLayout(new BorderLayout());
        frame.setSize(500, 500);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        // Initialize input field
        inputField = new JTextField(10);

        // Initialize number list and array
        numbers = new ArrayList<>();
        numberList = new JList<>(numbers.toArray(new Double[0]));
        JScrollPane scrollPane = new JScrollPane(numberList);
        scrollPane.setPreferredSize(new Dimension(150, 200));

        // Initialize buttons
        addButton = new JButton("Add");
        deleteButton = new JButton("Delete");
        editButton = new JButton("Edit");

        // Initialize chart panel
        chartPanel = new ChartPanel(numbers);

        // Add action listener to add button
        addButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                try {
                    double number = Double.parseDouble(inputField.getText());
                    numbers.add(number);
                    numberList.setListData(numbers.toArray(new Double[0]));
                    chartPanel.repaint();
                } catch (NumberFormatException ex) {
                    JOptionPane.showMessageDialog(frame, "Please enter a valid number.");
                }
            }
        });

        // Add action listener to delete button
        deleteButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                int index = numberList.getSelectedIndex();
                if (index != -1) {
                    numbers.remove(index);
                    numberList.setListData(numbers.toArray(new Double[0]));
                    chartPanel.repaint();
                } else {
                    JOptionPane.showMessageDialog(frame, "Please select a number to delete.");
                }
            }
        });

        // Add action listener to edit button
        editButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                int index = numberList.getSelectedIndex();
                if (index != -1) {
                    try {
                        double number = Double.parseDouble(inputField.getText());
                        numbers.set(index, number);
                        numberList.setListData(numbers.toArray(new Double[0]));
                        chartPanel.repaint();
                    } catch (NumberFormatException ex) {
                        JOptionPane.showMessageDialog(frame, "Please enter a valid number.");
                    }
                } else {
                    JOptionPane.showMessageDialog(frame, "Please select a number to edit.");
                }
            }
        });

        // Add input field, buttons, scrollPane and chart panel to the frame
        frame.add(inputField, BorderLayout.NORTH);
        frame.add(chartPanel, BorderLayout.CENTER);
        frame.add(scrollPane, BorderLayout.WEST);
        JPanel buttonPanel = new JPanel();
        buttonPanel.add(addButton);
        buttonPanel.add(deleteButton);
        buttonPanel.add(editButton);
        frame.add(buttonPanel, BorderLayout.SOUTH);

        // Show frame
        frame.setVisible(true);
    }

    public static void main(String[] args) {
        new Main();
    }

    // Create ChartPanel class
    class ChartPanel extends JPanel {
        private ArrayList<Double> numbers;
        private Color[] colors = {Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PINK, Color.CYAN};

        public ChartPanel(ArrayList<Double> numbers) {
            this.numbers = numbers;
        }

        @Override
        public void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2d = (Graphics2D) g;
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int total = 0;
            for (double number : numbers) {
                total += number;
            }

            int startAngle = 0;
            for (int i = 0; i < numbers.size(); i++) {
                double number = numbers.get(i);
                int angle = (int) (number / total * 360);
                g2d.setColor(colors[i % colors.length]);
                g2d.fillArc(10, 10, getWidth() - 20, getHeight() - 20, startAngle, angle);
                startAngle += angle;
            }
        }
    }
}
