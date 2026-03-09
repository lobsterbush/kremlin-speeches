"""
Geographic classification of Kremlin speeches
Classifies by location (where) and participants (who) at continent/region level
"""

import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeographicClassifier:
    """Classify speeches by geographic location and participant origin"""
    
    def __init__(self):
        # Location keywords for regions/continents
        self.location_keywords = {
            'Europe': [
                'Moscow', 'St Petersburg', 'Kremlin', 'Russia', 'Sochi', 'Kazan', 'Yekaterinburg',
                'Brussels', 'Paris', 'Berlin', 'London', 'Rome', 'Madrid', 'Warsaw', 'Prague',
                'Vienna', 'Budapest', 'Belgrade', 'Athens', 'Helsinki', 'Stockholm', 'Oslo',
                'Copenhagen', 'Amsterdam', 'Minsk', 'Kiev', 'Kyiv', 'Ukraine', 'Belarus',
                'Moldova', 'Bucharest', 'Sofia', 'Zagreb', 'Geneva', 'Zurich'
            ],
            'Asia': [
                'Beijing', 'China', 'Tokyo', 'Japan', 'Seoul', 'South Korea', 'Delhi', 'India',
                'Mumbai', 'Singapore', 'Bangkok', 'Thailand', 'Vietnam', 'Hanoi', 'Manila',
                'Jakarta', 'Malaysia', 'Vladivostok', 'Ulan Bator', 'Mongolia', 'Tehran',
                'Ankara', 'Turkey', 'Istanbul', 'Kazakhstan', 'Astana', 'Tashkent', 'Uzbekistan',
                'Dushanbe', 'Tajikistan', 'Bishkek', 'Kyrgyzstan', 'Turkmenistan', 'Ashgabat'
            ],
            'Middle East': [
                'Syria', 'Damascus', 'Iran', 'Tehran', 'Israel', 'Tel Aviv', 'Jerusalem',
                'Saudi Arabia', 'Riyadh', 'UAE', 'Dubai', 'Abu Dhabi', 'Qatar', 'Doha',
                'Kuwait', 'Bahrain', 'Oman', 'Yemen', 'Iraq', 'Baghdad', 'Jordan', 'Amman',
                'Lebanon', 'Beirut', 'Egypt', 'Cairo'
            ],
            'Africa': [
                'South Africa', 'Johannesburg', 'Cape Town', 'Egypt', 'Cairo', 'Nigeria',
                'Ethiopia', 'Kenya', 'Nairobi', 'Morocco', 'Algeria', 'Tunisia', 'Libya',
                'Sudan', 'Zimbabwe', 'Angola', 'Mozambique'
            ],
            'North America': [
                'United States', 'USA', 'Washington', 'New York', 'America', 'Canada',
                'Ottawa', 'Toronto', 'Mexico', 'Mexico City'
            ],
            'South America': [
                'Brazil', 'Brasilia', 'Argentina', 'Buenos Aires', 'Chile', 'Santiago',
                'Peru', 'Lima', 'Colombia', 'Bogota', 'Venezuela', 'Caracas', 'Ecuador'
            ],
            'Central Asia': [
                'Kazakhstan', 'Astana', 'Uzbekistan', 'Tashkent', 'Kyrgyzstan', 'Bishkek',
                'Tajikistan', 'Dushanbe', 'Turkmenistan', 'Ashgabat', 'Afghanistan', 'Kabul'
            ],
            'Oceania': [
                'Australia', 'Sydney', 'Canberra', 'New Zealand', 'Wellington', 'Papua New Guinea'
            ]
        }
        
        # Country/organization to region mapping for participants
        self.participant_keywords = {
            'European': [
                'Germany', 'German', 'France', 'French', 'UK', 'British', 'Britain', 'Italy',
                'Italian', 'Spain', 'Spanish', 'Poland', 'Polish', 'EU', 'European Union',
                'Netherlands', 'Dutch', 'Belgium', 'Austrian', 'Austria', 'Switzerland',
                'Swiss', 'Sweden', 'Swedish', 'Norway', 'Norwegian', 'Denmark', 'Finnish',
                'Finland', 'Greece', 'Greek', 'Portugal', 'Czech', 'Hungary', 'Hungarian',
                'Romania', 'Bulgaria', 'Serbia', 'Croatia', 'Ukraine', 'Ukrainian', 'Belarus',
                'Belarusian'
            ],
            'Asian': [
                'China', 'Chinese', 'Japan', 'Japanese', 'Korea', 'Korean', 'India', 'Indian',
                'Vietnam', 'Vietnamese', 'Thailand', 'Singapore', 'Indonesia', 'Malaysian',
                'Philippines', 'Pakistan', 'Mongolian', 'Mongolia'
            ],
            'Middle Eastern': [
                'Syria', 'Syrian', 'Iran', 'Iranian', 'Israel', 'Israeli', 'Saudi', 'Turkey',
                'Turkish', 'UAE', 'Emirati', 'Qatar', 'Qatari', 'Kuwait', 'Kuwaiti', 'Iraq',
                'Iraqi', 'Jordan', 'Lebanese', 'Egypt', 'Egyptian', 'Palestinian'
            ],
            'African': [
                'South Africa', 'Nigerian', 'Ethiopia', 'Kenyan', 'Morocco', 'Moroccan',
                'Algeria', 'Algerian', 'Tunisia', 'Tunisian', 'Libya', 'Libyan', 'Sudan',
                'Zimbabwe', 'Angola', 'African'
            ],
            'North American': [
                'USA', 'American', 'United States', 'Canada', 'Canadian', 'Mexico', 'Mexican'
            ],
            'South American': [
                'Brazil', 'Brazilian', 'Argentina', 'Argentine', 'Chile', 'Chilean', 'Peru',
                'Peruvian', 'Colombia', 'Colombian', 'Venezuela', 'Venezuelan', 'Ecuador'
            ],
            'Central Asian': [
                'Kazakhstan', 'Kazakh', 'Uzbekistan', 'Uzbek', 'Kyrgyzstan', 'Kyrgyz',
                'Tajikistan', 'Tajik', 'Turkmenistan', 'Turkmen', 'Afghanistan', 'Afghan'
            ],
            'Oceanian': [
                'Australia', 'Australian', 'New Zealand', 'Papua New Guinea'
            ],
            'International': [
                'United Nations', 'UN', 'NATO', 'BRICS', 'G20', 'G8', 'SCO', 'CIS',
                'Commonwealth', 'ASEAN', 'APEC', 'WTO', 'IMF', 'World Bank'
            ]
        }
    
    def classify_location(self, location_text, title_text=""):
        """Classify geographic region based on location field"""
        if not location_text:
            location_text = ""
        
        combined_text = f"{location_text} {title_text}".lower()
        
        # Check each region
        regions_found = []
        for region, keywords in self.location_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    regions_found.append(region)
                    break
        
        # Return first match or 'Russia/Domestic' as default
        if regions_found:
            # If Europe found and it's in Russia, classify as Russia/Domestic
            if 'Europe' in regions_found and any(k.lower() in combined_text for k in 
                ['moscow', 'st petersburg', 'kremlin', 'sochi', 'kazan', 'yekaterinburg']):
                return 'Russia/Domestic'
            return regions_found[0]
        
        # Default to Russia/Domestic if location contains Russian cities or is empty
        return 'Russia/Domestic'
    
    def classify_participants(self, title, speakers, content):
        """Classify participants' geographic origin"""
        # Handle NaN/missing values
        title = str(title) if title and title == title else ""
        speakers = str(speakers) if speakers and speakers == speakers else ""
        content = str(content) if content and content == content else ""
        
        combined_text = f"{title} {speakers} {content[:500]}".lower()  # Use first 500 chars of content
        
        regions_found = set()
        for region, keywords in self.participant_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    regions_found.add(region)
                    break
        
        # Default to Russian if no other participants found
        if not regions_found:
            return 'Russian'
        
        # If multiple regions, join them
        return '; '.join(sorted(regions_found))
    
    def classify_dataset(self, input_file, output_file):
        """Classify all speeches in dataset"""
        logger.info(f"Loading data from {input_file}")
        df = pd.read_csv(input_file)
        
        logger.info(f"Classifying {len(df)} speeches...")
        
        # Apply classifications
        df['location_region'] = df.apply(
            lambda row: self.classify_location(
                row.get('location', ''), 
                row.get('title', '')
            ), 
            axis=1
        )
        
        df['participant_region'] = df.apply(
            lambda row: self.classify_participants(
                row.get('title', ''),
                row.get('speakers', ''),
                row.get('content', '')
            ),
            axis=1
        )
        
        # Save classified dataset
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Saved classified data to {output_file}")
        
        # Print summary statistics
        print("\n=== Classification Summary ===")
        print("\nLocation Region Distribution:")
        print(df['location_region'].value_counts())
        print("\nParticipant Region Distribution:")
        print(df['participant_region'].value_counts())
        
        return df


if __name__ == "__main__":
    classifier = GeographicClassifier()
    
    # Classify the scraped data
    df = classifier.classify_dataset(
        input_file="kremlin_speeches_raw.csv",
        output_file="kremlin_speeches_classified.csv"
    )
    
    print(f"\nClassification complete! Results saved to kremlin_speeches_classified.csv")
